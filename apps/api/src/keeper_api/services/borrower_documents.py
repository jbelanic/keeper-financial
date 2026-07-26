from __future__ import annotations

import hashlib
import os
import uuid
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import BinaryIO, cast

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
    BorrowerDocument,
)
from keeper_api.services.borrower_crypto import (
    BorrowerCryptoState,
    BorrowerDecryptionError,
    EncryptedEnvelope,
    decrypt_payload,
    encrypt_payload,
)
from keeper_api.services.candidate_files import (
    DocumentPolicy,
    DocumentRejected,
    validate_document_bytes,
)
from keeper_api.services.malware_scanner import MalwareScannerUnavailable, build_malware_scanner

BORROWER_DOCUMENT_POLICY = DocumentPolicy(
    maximum_bytes=10 * 1024 * 1024,
    extension_mime_types={
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
)
MAX_BORROWER_ENCRYPTED_BYTES = BORROWER_DOCUMENT_POLICY.maximum_bytes + 16


class BorrowerDocumentRejected(ValueError):
    def __init__(self, code: str, *, status_code: int = 422) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code


class BorrowerDocumentStorageError(ValueError):
    pass


@dataclass(frozen=True)
class BorrowerStoredObject:
    object_key: str


@dataclass(frozen=True)
class BorrowerDocumentDownload:
    filename: str
    content_type: str
    content: bytes


def _put_borrower_object(
    settings: Settings,
    *,
    object_key: str,
    content: bytes,
    content_type: str,
) -> BorrowerStoredObject:
    if settings.storage_backend == "local":
        if settings.app_env != "local":
            raise BorrowerDocumentStorageError("storage_unavailable")
        root = settings.local_storage_path.resolve()
        destination = (root / object_key).resolve()
        if root not in destination.parents:
            raise BorrowerDocumentStorageError("storage_unavailable")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
        except OSError as exc:
            with suppress(OSError):
                destination.unlink(missing_ok=True)
            raise BorrowerDocumentStorageError("storage_unavailable") from exc
        return BorrowerStoredObject(object_key=object_key)

    client_options = {
        "aws_access_key_id": settings.s3_access_key_id,
        "aws_secret_access_key": (
            settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key
            else None
        ),
        "region_name": settings.s3_region,
        "config": Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    }
    client = boto3.client("s3", endpoint_url=settings.s3_endpoint_url, **client_options)
    try:
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=object_key,
            Body=content,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise BorrowerDocumentStorageError("storage_unavailable") from exc
    return BorrowerStoredObject(object_key=object_key)


def _get_borrower_object(settings: Settings, *, object_key: str) -> bytes:
    if settings.storage_backend == "local":
        root = settings.local_storage_path.resolve()
        path = (root / object_key).resolve()
        if root not in path.parents or not path.is_file():
            raise BorrowerDocumentStorageError("storage_unavailable")
        try:
            if path.stat().st_size > MAX_BORROWER_ENCRYPTED_BYTES:
                raise BorrowerDocumentStorageError("storage_unavailable")
            return path.read_bytes()
        except OSError as exc:
            raise BorrowerDocumentStorageError("storage_unavailable") from exc

    client_options = {
        "aws_access_key_id": settings.s3_access_key_id,
        "aws_secret_access_key": (
            settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key
            else None
        ),
        "region_name": settings.s3_region,
        "config": Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    }
    client = boto3.client("s3", endpoint_url=settings.s3_endpoint_url, **client_options)
    try:
        head = client.head_object(Bucket=settings.s3_bucket, Key=object_key)
        if (
            int(head.get("ContentLength", MAX_BORROWER_ENCRYPTED_BYTES + 1))
            > MAX_BORROWER_ENCRYPTED_BYTES
        ):
            raise BorrowerDocumentStorageError("storage_unavailable")
        response = client.get_object(Bucket=settings.s3_bucket, Key=object_key)
        body = response["Body"]
        try:
            content = cast(bytes, body.read(MAX_BORROWER_ENCRYPTED_BYTES + 1))
            if len(content) > MAX_BORROWER_ENCRYPTED_BYTES:
                raise BorrowerDocumentStorageError("storage_unavailable")
            return content
        finally:
            body.close()
    except (BotoCoreError, ClientError, KeyError, OSError) as exc:
        raise BorrowerDocumentStorageError("storage_unavailable") from exc


def delete_borrower_object(settings: Settings, object_key: str) -> None:
    if settings.storage_backend == "local":
        root = settings.local_storage_path.resolve()
        path = (root / object_key).resolve()
        if root not in path.parents:
            return
        with suppress(OSError):
            path.unlink(missing_ok=True)
        return

    client_options = {
        "aws_access_key_id": settings.s3_access_key_id,
        "aws_secret_access_key": (
            settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key
            else None
        ),
        "region_name": settings.s3_region,
        "config": Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    }
    client = boto3.client("s3", endpoint_url=settings.s3_endpoint_url, **client_options)
    with suppress(BotoCoreError, ClientError):
        client.delete_object(Bucket=settings.s3_bucket, Key=object_key)


def put_encrypted_borrower_object(
    settings: Settings,
    *,
    prefix: str,
    content: bytes,
    content_type: str,
) -> BorrowerStoredObject:
    object_key = f"borrower/{prefix.strip('/')}/{uuid.uuid4().hex}"
    return _put_borrower_object(
        settings,
        object_key=object_key,
        content=content,
        content_type=content_type,
    )


def upload_document(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
    capability_session_id: uuid.UUID,
    file_stream: BinaryIO,
    filename: str | None,
    mime_type: str | None,
    settings: Settings,
) -> BorrowerDocument:
    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    if application.capability_session_id != capability_session_id:
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    if application.lifecycle_status != BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise BorrowerDocumentRejected("document_uploads_unavailable", status_code=409)
    if crypto_state is None:
        raise BorrowerDocumentStorageError("borrower_cryptography_unavailable")

    try:
        content = file_stream.read(BORROWER_DOCUMENT_POLICY.maximum_bytes + 1)
        validated = validate_document_bytes(
            content,
            original_filename=filename,
            declared_content_type=mime_type,
            policy=BORROWER_DOCUMENT_POLICY,
        )
    except DocumentRejected as exc:
        status_code = 413 if exc.code == "file_too_large" else 422
        raise BorrowerDocumentRejected(exc.code, status_code=status_code) from exc

    try:
        scanner = build_malware_scanner(settings)
        decision = scanner.scan(validated.content)
    except MalwareScannerUnavailable as exc:
        raise BorrowerDocumentStorageError("scanner_unavailable") from exc
    if decision.status != "clean":
        raise BorrowerDocumentRejected("malware_detected", status_code=422)

    sha256 = hashlib.sha256(validated.content).hexdigest()
    envelope = encrypt_payload(
        state=crypto_state,
        plaintext=validated.content,
        application_id=str(application_id),
        purpose="borrower_document",
        schema_version="1.0",
        payload_revision=application.revision,
    )

    stored = put_encrypted_borrower_object(
        settings,
        prefix=f"documents/{application_id}",
        content=envelope.ciphertext,
        content_type="application/octet-stream",
    )
    document = BorrowerDocument(
        application_id=application_id,
        filename=validated.filename,
        mime_type=validated.content_type,
        size_bytes=len(validated.content),
        sha256=sha256,
        minio_object_key=stored.object_key,
        encryption_key_id=envelope.key_id,
        encryption_nonce=envelope.nonce,
        encryption_payload_revision=application.revision,
        scan_status="clean",
        scan_timestamp=datetime.now(UTC),
        uploaded_by="borrower",
        capability_session_id=capability_session_id,
    )
    try:
        db.add(document)
        application.last_activity_at = datetime.now(UTC)
        db.flush()
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        delete_borrower_object(settings, stored.object_key)
        raise
    return document


def list_document_metadata(db: Session, application_id: uuid.UUID) -> list[BorrowerDocument]:
    return (
        db.query(BorrowerDocument)
        .filter(BorrowerDocument.application_id == application_id)
        .order_by(BorrowerDocument.created_at.asc(), BorrowerDocument.id.asc())
        .all()
    )


def download_document(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
    document_id: uuid.UUID,
    settings: Settings,
) -> BorrowerDocumentDownload:
    if crypto_state is None:
        raise BorrowerDocumentStorageError("borrower_cryptography_unavailable")

    document = db.get(BorrowerDocument, document_id)
    if document is None or document.application_id != application_id:
        raise BorrowerDocumentRejected("document_not_found", status_code=404)
    if document.encryption_payload_revision is None:
        raise BorrowerDocumentStorageError("storage_unavailable")

    ciphertext = _get_borrower_object(settings, object_key=document.minio_object_key)
    try:
        plaintext = decrypt_payload(
            state=crypto_state,
            envelope=EncryptedEnvelope(
                format_version=1,
                key_id=document.encryption_key_id,
                nonce=document.encryption_nonce,
                ciphertext=ciphertext,
            ),
            application_id=str(application_id),
            purpose="borrower_document",
            schema_version="1.0",
            payload_revision=document.encryption_payload_revision,
        )
    except BorrowerDecryptionError as exc:
        raise BorrowerDocumentStorageError("storage_unavailable") from exc

    if hashlib.sha256(plaintext).hexdigest() != document.sha256:
        raise BorrowerDocumentStorageError("storage_unavailable")

    return BorrowerDocumentDownload(
        filename=document.filename,
        content_type=document.mime_type,
        content=plaintext,
    )
