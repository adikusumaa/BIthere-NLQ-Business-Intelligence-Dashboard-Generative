"""
Unit tests for SecretVault (Fernet encryption).
"""

import pytest

from app.core.encryption import vault, EncryptionError


def test_encrypt_returns_bytes_and_differs_from_plaintext():
    original = "gsk_test_1234567890abcdef"
    token = vault.encrypt(original)

    assert isinstance(token, bytes)
    assert token != original.encode()
    assert len(token) > 50


def test_decrypt_restores_original():
    original = "gsk_test_1234567890abcdef"
    token = vault.encrypt(original)

    restored = vault.decrypt(token)
    assert restored == original


def test_mask_hides_middle_and_keeps_edges():
    value = "gsk_test_1234567890abcdef"
    masked = vault.mask(value)

    assert masked.startswith("gsk_")
    assert masked.endswith("cdef")
    assert "*" in masked
    assert value not in masked


def test_decrypt_rejects_tampered_token():
    original = "gsk_test_1234567890abcdef"
    token = vault.encrypt(original)
    tampered = token[:-5] + b"XXXXX"

    with pytest.raises(EncryptionError):
        vault.decrypt(tampered)


def test_encrypt_rejects_none():
    with pytest.raises(EncryptionError):
        vault.encrypt(None)


def test_decrypt_rejects_none():
    with pytest.raises(EncryptionError):
        vault.decrypt(None)