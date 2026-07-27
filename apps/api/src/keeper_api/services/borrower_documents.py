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
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
    BorrowerDocument,
)
from keeper_api.services.audit import AuditService
from keeper_api.services.borrower_applications import (
    borrower_draft_expired,
    record_borrower_draft_activity,
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

BORROWER_DOCUMENT_MAXIMUM_BYTES = 25 * 1024 * 1024
BORROWER_DOCUMENT_CATEGORIES = {
    "identification",
    "income_employment",
    "banking_investment",
    "down_payment",
    "property",
    "tax",
    "credit_liability",
    "other",
}
BORROWER_DOCUMENT_POLICY = DocumentPolicy(
    maximum_bytes=BORROWER_DOCUMENT_MAXIMUM_BYTES,
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
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise BorrowerDocumentStorageError("storage_unavailable") from exc
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
    try:
        client.delete_object(Bucket=settings.s3_bucket, Key=object_key)
    except (BotoCoreError, ClientError) as exc:
        raise BorrowerDocumentStorageError("storage_unavailable") from exc


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
    category: str,
    description: str | None,
    settings: Settings,
    request_id: str | None = None,
) -> BorrowerDocument:
    application = db.scalar(
        select(BorrowerApplication)
        .where(BorrowerApplication.id == application_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if application is None:
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    if application.capability_session_id != capability_session_id:
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    if application.lifecycle_status != BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise BorrowerDocumentRejected("document_uploads_unavailable", status_code=409)
    if borrower_draft_expired(application):
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    if crypto_state is None:
        raise BorrowerDocumentStorageError("borrower_cryptography_unavailable")
    normalized_description = description.strip() if description else None
    if category not in BORROWER_DOCUMENT_CATEGORIES:
        raise BorrowerDocumentRejected("invalid_category")
    if category == "other" and not normalized_description:
        raise BorrowerDocumentRejected("description_required")
    if category != "other" and normalized_description:
        raise BorrowerDocumentRejected("description_not_allowed")
    if normalized_description and len(normalized_description) > 200:
        raise BorrowerDocumentRejected("description_too_long")
    document_count, total_bytes = db.execute(
        select(
            func.count(BorrowerDocument.id),
            func.coalesce(func.sum(BorrowerDocument.size_bytes), 0),
        ).where(BorrowerDocument.application_id == application_id)
    ).one()
    if document_count >= settings.borrower_max_document_count:
        raise BorrowerDocumentRejected("document_count_limit", status_code=413)

    try:
        policy = DocumentPolicy(
            maximum_bytes=settings.borrower_max_document_bytes,
            extension_mime_types=BORROWER_DOCUMENT_POLICY.extension_mime_types,
        )
        content = file_stream.read(policy.maximum_bytes + 1)
        validated = validate_document_bytes(
            content,
            original_filename=filename,
            declared_content_type=mime_type,
            policy=policy,
        )
    except DocumentRejected as exc:
        status_code = 413 if exc.code == "file_too_large" else 422
        raise BorrowerDocumentRejected(exc.code, status_code=status_code) from exc
    if int(total_bytes) + len(validated.content) > settings.borrower_max_total_document_bytes:
        raise BorrowerDocumentRejected("aggregate_size_limit", status_code=413)

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
        prefix="documents",
        content=envelope.ciphertext,
        content_type="application/octet-stream",
    )
    document = BorrowerDocument(
        application_id=application_id,
        filename=validated.filename,
        category=category,
        description=normalized_description,
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
        record_borrower_draft_activity(application)
        db.flush()
        db.refresh(document)
        AuditService(db).record(
            "borrower_document_uploaded",
            "borrower_document",
            document.id,
            request_id=request_id,
            safe_metadata={
                "result": "success",
                "scan_status": "clean",
                "category": category,
            },
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        try:
            delete_borrower_object(settings, stored.object_key)
        except BorrowerDocumentStorageError as cleanup_exc:
            raise BorrowerDocumentStorageError("storage_cleanup_unavailable") from cleanup_exc
        raise BorrowerDocumentStorageError("storage_unavailable") from exc
    return document


def delete_draft_document(
    db: Session,
    application_id: uuid.UUID,
    capability_session_id: uuid.UUID,
    document_id: uuid.UUID,
    settings: Settings,
    request_id: str | None = None,
) -> None:
    application = db.scalar(
        select(BorrowerApplication)
        .where(BorrowerApplication.id == application_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if application is None or application.capability_session_id != capability_session_id:
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    if application.lifecycle_status != BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise BorrowerDocumentRejected("document_removal_unavailable", status_code=409)
    if borrower_draft_expired(application):
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    document = db.scalar(
        select(BorrowerDocument).where(
            BorrowerDocument.id == document_id,
            BorrowerDocument.application_id == application_id,
        )
    )
    if document is None:
        raise BorrowerDocumentRejected("document_not_found", status_code=404)
    object_key = document.minio_object_key
    if document.deletion_pending_at is None:
        document.deletion_pending_at = datetime.now(UTC)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise BorrowerDocumentStorageError("storage_unavailable") from exc

    delete_borrower_object(settings, object_key)

    application = db.scalar(
        select(BorrowerApplication)
        .where(BorrowerApplication.id == application_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if application is None:
        raise BorrowerDocumentRejected("application_not_found", status_code=404)
    document = db.scalar(
        select(BorrowerDocument)
        .where(
            BorrowerDocument.id == document_id,
            BorrowerDocument.application_id == application_id,
        )
        .with_for_update()
    )
    if document is None:
        db.commit()
        return
    try:
        AuditService(db).record(
            "borrower_document_removed",
            "borrower_document",
            document.id,
            request_id=request_id,
            safe_metadata={"result": "success"},
        )
        db.delete(document)
        record_borrower_draft_activity(application)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise BorrowerDocumentStorageError("storage_unavailable") from exc


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
    if document.deletion_pending_at is not None:
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
