"""Approved public agent photos (decision 56).

An administrator uploads one bounded JPEG/PNG through the administration
console. The bytes are validated, scanned by the configured malware scanner
(fail closed), and stored in the **private** MinIO bucket under the
``public/agent-photos/`` prefix. Nothing becomes anonymously readable: the only
way to fetch the object is the public read route, which serves that prefix and
nothing else, under an immutable cache header.

The agent profile keeps storing a public ``photo_url``. The URL this module
composes is stable and self-describing, so a profile's current photo can be
deleted when it is replaced without adding a second column.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import replace

from keeper_api.core.config import Settings
from keeper_api.services.candidate_files import (
    FIVE_MIB,
    DocumentPolicy,
    DocumentRejected,
    validate_document_bytes,
)
from keeper_api.services.malware_scanner import (
    MalwareScannerUnavailable,
    build_malware_scanner,
)
from keeper_api.services.storage import (
    PUBLIC_IMAGE_PREFIX,
    StorageError,
    StoredObject,
    build_storage,
)

PHOTO_ROUTE_PREFIX = "/api/v1/agent-photos/"
AGENT_PHOTO_POLICY = DocumentPolicy(
    maximum_bytes=FIVE_MIB,
    extension_mime_types={
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    },
)
_PHOTO_ID = re.compile(r"^[0-9a-f]{32}\.(?:jpg|png)$")


class AgentPhotoRejected(ValueError):
    """The upload is not an approved, well-formed agent photo."""

    def __init__(self, code: str) -> None:
        super().__init__("agent photo was rejected")
        self.code = code


def photo_id_for(object_key: str) -> str:
    return object_key.removeprefix(f"{PUBLIC_IMAGE_PREFIX}/")


def object_key_for(photo_id: str) -> str:
    if _PHOTO_ID.fullmatch(photo_id) is None:
        raise AgentPhotoRejected("invalid_photo_id")
    return f"{PUBLIC_IMAGE_PREFIX}/{photo_id}"


def photo_id_from_url(settings: Settings, url: str | None) -> str | None:
    """Return the Keeper-managed photo id inside `url`, or None if it is external."""
    if not url:
        return None
    base = f"{settings.public_site_base_url.rstrip('/')}{PHOTO_ROUTE_PREFIX}"
    if not url.startswith(base):
        return None
    candidate = url[len(base) :]
    return candidate if _PHOTO_ID.fullmatch(candidate) is not None else None


def photo_url(settings: Settings, photo_id: str) -> str:
    return f"{settings.public_site_base_url.rstrip('/')}{PHOTO_ROUTE_PREFIX}{photo_id}"


def store_agent_photo(
    settings: Settings,
    *,
    content: bytes,
    filename: str | None,
    content_type: str | None,
) -> StoredObject:
    """Validate, scan, and persist one approved public agent photo."""
    try:
        validated = validate_document_bytes(
            content,
            original_filename=filename,
            declared_content_type=content_type,
            policy=replace(AGENT_PHOTO_POLICY, maximum_bytes=settings.agent_photo_max_bytes),
        )
    except DocumentRejected as exc:
        raise AgentPhotoRejected(exc.code) from exc
    decision = build_malware_scanner(settings).scan(validated.content)
    if decision.status != "clean":
        raise AgentPhotoRejected("malware_detected")
    return build_storage(settings).put_public_image(
        validated.content,
        content_type=validated.content_type,
        maximum_bytes=settings.agent_photo_max_bytes,
    )


def read_agent_photo(settings: Settings, photo_id: str) -> tuple[bytes, str]:
    return build_storage(settings).read_public_image(object_key_for(photo_id))


def delete_agent_photo(settings: Settings, photo_id: str) -> None:
    try:
        build_storage(settings).delete_public_image(object_key_for(photo_id))
    except (AgentPhotoRejected, StorageError):
        # Replacing a photo must never fail because an old object is already gone.
        return


def audit_target_id(photo_id: str) -> uuid.UUID:
    return uuid.UUID(photo_id.split(".", 1)[0])


__all__ = [
    "AGENT_PHOTO_POLICY",
    "PHOTO_ROUTE_PREFIX",
    "AgentPhotoRejected",
    "MalwareScannerUnavailable",
    "audit_target_id",
    "delete_agent_photo",
    "object_key_for",
    "photo_id_for",
    "photo_id_from_url",
    "photo_url",
    "read_agent_photo",
    "store_agent_photo",
]
