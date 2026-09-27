from __future__ import annotations

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class CredentialError(ValueError):
    """Raised when an account credential cannot be encrypted or decrypted."""


def _fernet_key(raw_key: str) -> bytes:
    raw_key = raw_key.strip()
    if not raw_key:
        raise CredentialError("ACCOUNT_ENCRYPTION_KEY is required")
    try:
        decoded = base64.urlsafe_b64decode(raw_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        decoded = b""
    if len(decoded) == 32:
        return raw_key.encode("ascii")
    return base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode("utf-8")).digest())


def encrypt_secret(value: str, key: str) -> str:
    if not value:
        raise CredentialError("credential value must not be blank")
    return Fernet(_fernet_key(key)).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(ciphertext: str, key: str) -> str:
    if not ciphertext:
        raise CredentialError("encrypted credential must not be blank")
    try:
        return Fernet(_fernet_key(key)).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError) as exc:
        raise CredentialError("credential could not be decrypted") from exc
