from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class BorrowerCryptoConfigurationError(Exception):
    """Raised when borrower cryptography configuration is invalid."""

    def __init__(self, message: str = "borrower cryptography configuration is invalid"):
        super().__init__(message)


class BorrowerDecryptionError(Exception):
    """Raised when decryption fails due to wrong key, context, or tampered data."""

    def __init__(self, message: str = "decryption failed"):
        super().__init__(message)


@dataclass(frozen=True)
class EncryptedEnvelope:
    format_version: int
    key_id: str
    nonce: bytes
    ciphertext: bytes


ENVELOPE_FORMAT_VERSION = 1
NONCE_LENGTH = 12
KEY_LENGTH = 32
HMAC_KEY_LENGTH = 32


def _load_keyring_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise BorrowerCryptoConfigurationError()
    if not path.is_file():
        raise BorrowerCryptoConfigurationError()
    if path.is_symlink():
        raise BorrowerCryptoConfigurationError()

    try:
        stat = path.stat()
    except OSError:
        raise BorrowerCryptoConfigurationError() from None

    if stat.st_nlink != 1:
        raise BorrowerCryptoConfigurationError()

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raise BorrowerCryptoConfigurationError() from None

    import re

    key_pattern = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s*:')
    keys_match = re.search(r'"keys"\s*:\s*\{', content)
    if keys_match:
        keys_start = keys_match.end()
        brace_depth = 1
        keys_text_start = keys_start
        for i in range(keys_start, len(content)):
            if content[i] == "{":
                brace_depth += 1
            elif content[i] == "}":
                brace_depth -= 1
                if brace_depth == 0:
                    keys_text = content[keys_text_start:i]
                    break
        else:
            keys_text = ""

        seen_raw: list[str] = []
        for m in key_pattern.finditer(keys_text):
            raw = m.group(1)
            if raw.startswith("keys"):
                continue
            seen_raw.append(raw)
        if len(seen_raw) != len(set(seen_raw)):
            raise BorrowerCryptoConfigurationError()

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        raise BorrowerCryptoConfigurationError() from None

    if not isinstance(data, dict):
        raise BorrowerCryptoConfigurationError()

    if "version" not in data or "keys" not in data:
        raise BorrowerCryptoConfigurationError()

    if data["version"] != 1:
        raise BorrowerCryptoConfigurationError()

    keys = data["keys"]
    if not isinstance(keys, dict) or not keys:
        raise BorrowerCryptoConfigurationError()

    decoded_keys: dict[str, bytes] = {}

    for key_id, key_value in keys.items():
        if not isinstance(key_id, str) or not key_id.strip():
            raise BorrowerCryptoConfigurationError()

        if not isinstance(key_value, str):
            raise BorrowerCryptoConfigurationError()

        try:
            key_bytes = base64.b64decode(key_value)
        except Exception:
            raise BorrowerCryptoConfigurationError() from None

        if len(key_bytes) != KEY_LENGTH:
            raise BorrowerCryptoConfigurationError()

        decoded_keys[key_id] = key_bytes

    return {"version": data["version"], "keys": decoded_keys}


def _load_hmac_key_file(path: Path) -> bytes:
    if not path.exists():
        raise BorrowerCryptoConfigurationError()
    if not path.is_file():
        raise BorrowerCryptoConfigurationError()
    if path.is_symlink():
        raise BorrowerCryptoConfigurationError()

    try:
        stat = path.stat()
    except OSError:
        raise BorrowerCryptoConfigurationError() from None

    if stat.st_nlink != 1:
        raise BorrowerCryptoConfigurationError()

    try:
        content = path.read_bytes()
    except OSError:
        raise BorrowerCryptoConfigurationError() from None

    if len(content) != HMAC_KEY_LENGTH:
        raise BorrowerCryptoConfigurationError()

    return content


def _validate_origin(origin: str, production: bool) -> None:
    if not origin:
        raise BorrowerCryptoConfigurationError()

    from urllib.parse import urlparse

    try:
        parsed = urlparse(origin)
    except Exception:
        raise BorrowerCryptoConfigurationError() from None

    if not parsed.scheme or not parsed.hostname:
        raise BorrowerCryptoConfigurationError()

    if parsed.username or parsed.password:
        raise BorrowerCryptoConfigurationError()

    if parsed.query or parsed.fragment:
        raise BorrowerCryptoConfigurationError()

    if parsed.path and parsed.path != "/":
        raise BorrowerCryptoConfigurationError()

    if production:
        if parsed.scheme != "https":
            raise BorrowerCryptoConfigurationError()
        if parsed.hostname != "apply.keeperfinancial.ca":
            raise BorrowerCryptoConfigurationError()
        if parsed.port not in (None, 443):
            raise BorrowerCryptoConfigurationError()


@dataclass(frozen=True)
class BorrowerCryptoState:
    keyring: dict[str, bytes]
    active_key_id: str
    hmac_key: bytes
    borrower_origin: str


def load_borrower_crypto_state(
    keyring_path: Path,
    hmac_key_path: Path,
    active_key_id: str,
    borrower_origin: str,
    production: bool = False,
) -> BorrowerCryptoState:
    _validate_origin(borrower_origin, production)

    try:
        keyring_data = _load_keyring_file(keyring_path)
    except BorrowerCryptoConfigurationError:
        raise

    if active_key_id not in keyring_data["keys"]:
        raise BorrowerCryptoConfigurationError()

    try:
        hmac_key = _load_hmac_key_file(hmac_key_path)
    except BorrowerCryptoConfigurationError:
        raise

    return BorrowerCryptoState(
        keyring=keyring_data["keys"],
        active_key_id=active_key_id,
        hmac_key=hmac_key,
        borrower_origin=borrower_origin,
    )


def encrypt_payload(
    state: BorrowerCryptoState,
    plaintext: bytes,
    application_id: str,
    purpose: str,
    schema_version: str,
    payload_revision: int,
) -> EncryptedEnvelope:
    key_id = state.active_key_id
    key_bytes = state.keyring[key_id]

    nonce = secrets.token_bytes(NONCE_LENGTH)

    aad = _build_aad(
        format_version=ENVELOPE_FORMAT_VERSION,
        purpose=purpose,
        application_id=application_id,
        schema_version=schema_version,
        payload_revision=payload_revision,
        key_id=key_id,
    )

    aesgcm = AESGCM(key_bytes)
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

    return EncryptedEnvelope(
        format_version=ENVELOPE_FORMAT_VERSION,
        key_id=key_id,
        nonce=nonce,
        ciphertext=ciphertext,
    )


def decrypt_payload(
    state: BorrowerCryptoState,
    envelope: EncryptedEnvelope,
    application_id: str,
    purpose: str,
    schema_version: str,
    payload_revision: int,
) -> bytes:
    if envelope.format_version != ENVELOPE_FORMAT_VERSION:
        raise BorrowerDecryptionError()

    if envelope.key_id not in state.keyring:
        raise BorrowerDecryptionError()

    key_bytes = state.keyring[envelope.key_id]

    aad = _build_aad(
        format_version=envelope.format_version,
        purpose=purpose,
        application_id=application_id,
        schema_version=schema_version,
        payload_revision=payload_revision,
        key_id=envelope.key_id,
    )

    try:
        aesgcm = AESGCM(key_bytes)
        plaintext = aesgcm.decrypt(envelope.nonce, envelope.ciphertext, aad)
    except Exception:
        raise BorrowerDecryptionError() from None

    return plaintext


def _build_aad(
    format_version: int,
    purpose: str,
    application_id: str,
    schema_version: str,
    payload_revision: int,
    key_id: str,
) -> bytes:
    aad_data = {
        "format_version": format_version,
        "purpose": purpose,
        "application_id": application_id,
        "schema_version": schema_version,
        "payload_revision": payload_revision,
        "key_id": key_id,
    }
    return json.dumps(aad_data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_capability_digest(capability: str, hmac_key: bytes) -> str:
    return hmac.new(hmac_key, capability.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_capability_digest(capability: str, stored_digest: str, hmac_key: bytes) -> bool:
    computed = compute_capability_digest(capability, hmac_key)
    return hmac.compare_digest(computed, stored_digest)


def generate_capability() -> str:
    return secrets.token_hex(32)


def encrypt_sin(
    state: BorrowerCryptoState,
    sin: str,
    application_id: str,
    payload_revision: int,
) -> tuple[bytes, bytes]:
    nonce = secrets.token_bytes(NONCE_LENGTH)

    aad = json.dumps(
        {
            "purpose": "sin",
            "application_id": application_id,
            "payload_revision": payload_revision,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    key_id = state.active_key_id
    key_bytes = state.keyring[key_id]

    aesgcm = AESGCM(key_bytes)
    ciphertext = aesgcm.encrypt(nonce, sin.encode("utf-8"), aad)

    return ciphertext, nonce


def decrypt_sin(
    state: BorrowerCryptoState,
    ciphertext: bytes,
    nonce: bytes,
    application_id: str,
    payload_revision: int,
    key_id: str,
) -> str:
    if key_id not in state.keyring:
        raise BorrowerDecryptionError()

    key_bytes = state.keyring[key_id]

    aad = json.dumps(
        {
            "purpose": "sin",
            "application_id": application_id,
            "payload_revision": payload_revision,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    try:
        aesgcm = AESGCM(key_bytes)
        plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception:
        raise BorrowerDecryptionError() from None

    return plaintext.decode("utf-8")
