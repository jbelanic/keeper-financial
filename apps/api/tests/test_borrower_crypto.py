from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path

import pytest

from keeper_api.services.borrower_crypto import (
    BorrowerCryptoConfigurationError,
    BorrowerCryptoState,
    BorrowerDecryptionError,
    compute_capability_digest,
    decrypt_payload,
    decrypt_sin,
    encrypt_payload,
    encrypt_sin,
    generate_capability,
    load_borrower_crypto_state,
    verify_capability_digest,
)


@pytest.fixture
def test_keys() -> dict[str, bytes]:
    return {
        "v1": os.urandom(32),
        "v2": os.urandom(32),
    }


@pytest.fixture
def test_hmac_key() -> bytes:
    return os.urandom(32)


@pytest.fixture
def keyring_file(test_keys: dict[str, bytes]) -> Path:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        keyring_data = {
            "version": 1,
            "keys": {k: base64.b64encode(v).decode() for k, v in test_keys.items()},
        }
        json.dump(keyring_data, f)
        f.flush()
        return Path(f.name)


@pytest.fixture
def hmac_key_file(test_hmac_key: bytes) -> Path:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(test_hmac_key)
        f.flush()
        return Path(f.name)


@pytest.fixture
def crypto_state(
    keyring_file: Path,
    hmac_key_file: Path,
    test_keys: dict[str, bytes],
    test_hmac_key: bytes,
) -> BorrowerCryptoState:
    return load_borrower_crypto_state(
        keyring_path=keyring_file,
        hmac_key_path=hmac_key_file,
        active_key_id="v1",
        borrower_origin="https://apply.keeperfinancial.ca",
        production=False,
    )


class TestAESGCMRoundTrip:
    def test_encrypt_decrypt_round_trip(self, crypto_state: BorrowerCryptoState) -> None:
        plaintext = b"test borrower application payload"
        application_id = "test-app-id-123"
        purpose = "borrower_application"
        schema_version = "1.0"
        payload_revision = 1

        envelope = encrypt_payload(
            state=crypto_state,
            plaintext=plaintext,
            application_id=application_id,
            purpose=purpose,
            schema_version=schema_version,
            payload_revision=payload_revision,
        )

        decrypted = decrypt_payload(
            state=crypto_state,
            envelope=envelope,
            application_id=application_id,
            purpose=purpose,
            schema_version=schema_version,
            payload_revision=payload_revision,
        )

        assert decrypted == plaintext

    def test_nonce_uniqueness(self, crypto_state: BorrowerCryptoState) -> None:
        plaintext = b"test payload"
        nonces = set()

        for _ in range(100):
            envelope = encrypt_payload(
                state=crypto_state,
                plaintext=plaintext,
                application_id="app-1",
                purpose="test",
                schema_version="1.0",
                payload_revision=1,
            )
            nonces.add(envelope.nonce)

        assert len(nonces) == 100

    def test_wrong_key_rejection(self, test_keys: dict[str, bytes], test_hmac_key: bytes) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            keyring_data = {
                "version": 1,
                "keys": {k: base64.b64encode(v).decode() for k, v in test_keys.items()},
            }
            json.dump(keyring_data, f)
            f.flush()
            keyring_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            keyring_data_v2_only = {
                "version": 1,
                "keys": {"v2": base64.b64encode(test_keys["v2"]).decode()},
            }
            json.dump(keyring_data_v2_only, f)
            f.flush()
            keyring_path_v2 = Path(f.name)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_hmac_key)
            f.flush()
            hmac_path = Path(f.name)

        state1 = load_borrower_crypto_state(
            keyring_path=keyring_path,
            hmac_key_path=hmac_path,
            active_key_id="v1",
            borrower_origin="https://apply.keeperfinancial.ca",
            production=False,
        )

        state2 = load_borrower_crypto_state(
            keyring_path=keyring_path_v2,
            hmac_key_path=hmac_path,
            active_key_id="v2",
            borrower_origin="https://apply.keeperfinancial.ca",
            production=False,
        )

        envelope = encrypt_payload(
            state=state1,
            plaintext=b"secret data",
            application_id="app-1",
            purpose="test",
            schema_version="1.0",
            payload_revision=1,
        )

        with pytest.raises(BorrowerDecryptionError):
            decrypt_payload(
                state=state2,
                envelope=envelope,
                application_id="app-1",
                purpose="test",
                schema_version="1.0",
                payload_revision=1,
            )

    def test_wrong_context_rejection(self, crypto_state: BorrowerCryptoState) -> None:
        envelope = encrypt_payload(
            state=crypto_state,
            plaintext=b"secret data",
            application_id="app-1",
            purpose="test",
            schema_version="1.0",
            payload_revision=1,
        )

        with pytest.raises(BorrowerDecryptionError):
            decrypt_payload(
                state=crypto_state,
                envelope=envelope,
                application_id="app-2",
                purpose="test",
                schema_version="1.0",
                payload_revision=1,
            )

    def test_tampered_ciphertext_rejection(self, crypto_state: BorrowerCryptoState) -> None:
        envelope = encrypt_payload(
            state=crypto_state,
            plaintext=b"secret data",
            application_id="app-1",
            purpose="test",
            schema_version="1.0",
            payload_revision=1,
        )

        tampered_ciphertext = bytearray(envelope.ciphertext)
        tampered_ciphertext[0] ^= 0xFF

        from keeper_api.services.borrower_crypto import EncryptedEnvelope

        tampered_envelope = EncryptedEnvelope(
            format_version=envelope.format_version,
            key_id=envelope.key_id,
            nonce=envelope.nonce,
            ciphertext=bytes(tampered_ciphertext),
        )

        with pytest.raises(BorrowerDecryptionError):
            decrypt_payload(
                state=crypto_state,
                envelope=tampered_envelope,
                application_id="app-1",
                purpose="test",
                schema_version="1.0",
                payload_revision=1,
            )

    def test_key_rotation_read_compatibility(
        self, test_keys: dict[str, bytes], test_hmac_key: bytes
    ) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            keyring_data = {
                "version": 1,
                "keys": {k: base64.b64encode(v).decode() for k, v in test_keys.items()},
            }
            json.dump(keyring_data, f)
            f.flush()
            keyring_path = Path(f.name)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(test_hmac_key)
            f.flush()
            hmac_path = Path(f.name)

        state_v1 = load_borrower_crypto_state(
            keyring_path=keyring_path,
            hmac_key_path=hmac_path,
            active_key_id="v1",
            borrower_origin="https://apply.keeperfinancial.ca",
            production=False,
        )

        envelope = encrypt_payload(
            state=state_v1,
            plaintext=b"old key data",
            application_id="app-1",
            purpose="test",
            schema_version="1.0",
            payload_revision=1,
        )

        state_v2 = load_borrower_crypto_state(
            keyring_path=keyring_path,
            hmac_key_path=hmac_path,
            active_key_id="v2",
            borrower_origin="https://apply.keeperfinancial.ca",
            production=False,
        )

        decrypted = decrypt_payload(
            state=state_v2,
            envelope=envelope,
            application_id="app-1",
            purpose="test",
            schema_version="1.0",
            payload_revision=1,
        )

        assert decrypted == b"old key data"

    def test_secret_safe_errors(self, crypto_state: BorrowerCryptoState) -> None:
        from keeper_api.services.borrower_crypto import BorrowerCryptoConfigurationError

        with pytest.raises(BorrowerCryptoConfigurationError):
            load_borrower_crypto_state(
                keyring_path=Path("/nonexistent/keyring.json"),
                hmac_key_path=Path("/nonexistent/hmac.key"),
                active_key_id="v1",
                borrower_origin="https://apply.keeperfinancial.ca",
                production=False,
            )

    def test_capability_digest_computation(self, test_hmac_key: bytes) -> None:
        capability = generate_capability()
        digest = compute_capability_digest(capability, test_hmac_key)

        assert isinstance(digest, str)
        assert len(digest) == 64

    def test_capability_verification(self, test_hmac_key: bytes) -> None:
        capability = generate_capability()
        digest = compute_capability_digest(capability, test_hmac_key)

        assert verify_capability_digest(capability, digest, test_hmac_key)
        assert not verify_capability_digest("wrong_capability", digest, test_hmac_key)

    def test_sin_encryption_decryption(self, crypto_state: BorrowerCryptoState) -> None:
        sin = "123456789"
        application_id = "app-1"
        payload_revision = 1

        ciphertext, nonce = encrypt_sin(crypto_state, sin, application_id, payload_revision)

        decrypted = decrypt_sin(
            crypto_state,
            ciphertext,
            nonce,
            application_id,
            payload_revision,
            crypto_state.active_key_id,
        )

        assert decrypted == sin

    def test_generate_capability_uniqueness(self) -> None:
        capabilities = {generate_capability() for _ in range(1000)}
        assert len(capabilities) == 1000

    def test_keyring_duplicate_key_ids_rejection(self, test_hmac_key: bytes) -> None:
        with pytest.raises(BorrowerCryptoConfigurationError):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                keyring_content = '{"version":1,"keys":{"v1":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=","v1":"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="}}'
                f.write(keyring_content)
                f.flush()
                keyring_path = Path(f.name)

            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(test_hmac_key)
                f.flush()
                hmac_path = Path(f.name)

            load_borrower_crypto_state(
                keyring_path=keyring_path,
                hmac_key_path=hmac_path,
                active_key_id="v1",
                borrower_origin="https://apply.keeperfinancial.ca",
                production=False,
            )

    def test_keyring_symlink_rejection(self, test_hmac_key: bytes) -> None:
        with pytest.raises(BorrowerCryptoConfigurationError):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                keyring_data = {
                    "version": 1,
                    "keys": {"v1": base64.b64encode(os.urandom(32)).decode()},
                }
                json.dump(keyring_data, f)
                f.flush()
                keyring_path = Path(f.name)

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                symlink_path = Path(f.name)
            symlink_path.unlink()
            symlink_path.symlink_to(keyring_path)

            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(test_hmac_key)
                f.flush()
                hmac_path = Path(f.name)

            load_borrower_crypto_state(
                keyring_path=symlink_path,
                hmac_key_path=hmac_path,
                active_key_id="v1",
                borrower_origin="https://apply.keeperfinancial.ca",
                production=False,
            )
