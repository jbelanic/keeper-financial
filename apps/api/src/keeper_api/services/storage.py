from __future__ import annotations

import hashlib
import os
import uuid
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from keeper_api.core.config import Settings


class StorageError(ValueError):
    pass


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    sha256_digest: str
    size_bytes: int


class PrivateStorage(Protocol):
    def put(self, stream: BinaryIO, *, content_type: str) -> StoredObject: ...

    def authorized_download(self, object_key: str) -> str | Path: ...

    def delete(self, object_key: str) -> None: ...


def _read_limited(stream: BinaryIO, maximum: int) -> bytes:
    data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise StorageError("document exceeds the configured size limit")
    return data


class LocalPrivateStorage:
    def __init__(self, settings: Settings) -> None:
        if settings.app_env != "local" or settings.storage_backend != "local":
            raise StorageError("local document storage is available only in the local tier")
        self.settings = settings
        self.root = settings.local_storage_path.resolve()
        try:
            self.root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageError("private storage initialization failed") from exc

    def put(self, stream: BinaryIO, *, content_type: str) -> StoredObject:
        if content_type.lower() not in self.settings.allowed_mime_types:
            raise StorageError("document content type is not allowed")
        data = _read_limited(stream, self.settings.max_document_bytes)
        object_key = f"candidate/{uuid.uuid4().hex}"
        destination = (self.root / object_key).resolve()
        if self.root not in destination.parents:
            raise StorageError("invalid object key")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            descriptor = os.open(destination, flags, 0o600)
            with os.fdopen(descriptor, "wb") as file_handle:
                file_handle.write(data)
        except OSError as exc:
            with suppress(OSError):
                destination.unlink(missing_ok=True)
            raise StorageError("private storage write failed") from exc
        return StoredObject(object_key, hashlib.sha256(data).hexdigest(), len(data))

    def authorized_download(self, object_key: str) -> Path:
        path = (self.root / object_key).resolve()
        if self.root not in path.parents or not path.is_file():
            raise StorageError("private object was not found")
        return path

    def delete(self, object_key: str) -> None:
        path = (self.root / object_key).resolve()
        if self.root not in path.parents:
            raise StorageError("invalid object key")
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError("private storage deletion failed") from exc


class R2PrivateStorage:
    def __init__(self, settings: Settings) -> None:
        if settings.storage_backend != "r2":
            raise StorageError("R2 storage is not configured")
        self.settings = settings
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=(
                settings.r2_secret_access_key.get_secret_value()
                if settings.r2_secret_access_key
                else None
            ),
            region_name=settings.r2_region,
        )

    def put(self, stream: BinaryIO, *, content_type: str) -> StoredObject:
        if content_type.lower() not in self.settings.allowed_mime_types:
            raise StorageError("document content type is not allowed")
        data = _read_limited(stream, self.settings.max_document_bytes)
        object_key = f"candidate/{uuid.uuid4().hex}"
        try:
            self.client.put_object(
                Bucket=self.settings.r2_bucket,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("private storage write failed") from exc
        return StoredObject(object_key, hashlib.sha256(data).hexdigest(), len(data))

    def authorized_download(self, object_key: str) -> str:
        try:
            return str(
                self.client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.settings.r2_bucket, "Key": object_key},
                    ExpiresIn=self.settings.signed_url_ttl_seconds,
                )
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("private storage retrieval failed") from exc

    def delete(self, object_key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.settings.r2_bucket, Key=object_key)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("private storage deletion failed") from exc


def build_storage(settings: Settings) -> PrivateStorage:
    if settings.storage_backend == "local":
        return LocalPrivateStorage(settings)
    return R2PrivateStorage(settings)
