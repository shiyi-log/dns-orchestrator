import pytest

from backend.app.crypto import CredentialError, decrypt_secret, encrypt_secret


def test_secret_round_trip_does_not_store_plaintext():
    ciphertext = encrypt_secret("pat-value", "test-encryption-key")

    assert ciphertext != "pat-value"
    assert decrypt_secret(ciphertext, "test-encryption-key") == "pat-value"


def test_wrong_key_is_rejected():
    ciphertext = encrypt_secret("pat-value", "test-encryption-key")

    with pytest.raises(CredentialError):
        decrypt_secret(ciphertext, "different-key")
