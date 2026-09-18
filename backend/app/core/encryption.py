"""
Fernet-based symmetric encryption for workspace secrets.
Uses MASTER_ENCRYPTION_KEY from environment.
"""

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.logging import logger


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class SecretVault:
    """
    Symmetric encryption helper for workspace-level secrets.
    All API keys (Groq, Google, Pinecone, Slack, Email) are
    encrypted with this before being persisted to the database.
    """

    def __init__(self, master_key: str) -> None:
        if not master_key:
            raise EncryptionError("MASTER_ENCRYPTION_KEY is not set")
        try:
            self._fernet = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)
        except Exception as exc:
            raise EncryptionError(f"Invalid MASTER_ENCRYPTION_KEY format: {exc}") from exc

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt a plaintext string into Fernet token bytes."""
        if plaintext is None:
            raise EncryptionError("Cannot encrypt None")
        if not isinstance(plaintext, str):
            raise EncryptionError("Plaintext must be a string")
        try:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            logger.info("[PROCESS] Secret encrypted successfully")
            return token
        except Exception as exc:
            logger.error(f"[ERROR] Encryption failed: {exc}")
            raise EncryptionError(f"Encryption failed: {exc}") from exc

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt a Fernet token back into plaintext."""
        if ciphertext is None:
            raise EncryptionError("Cannot decrypt None")
        if isinstance(ciphertext, memoryview):
            ciphertext = bytes(ciphertext)
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise EncryptionError("Ciphertext must be bytes")
        try:
            plaintext = self._fernet.decrypt(bytes(ciphertext)).decode("utf-8")
            logger.info("[PROCESS] Secret decrypted successfully")
            return plaintext
        except InvalidToken as exc:
            logger.error("[ERROR] Invalid token: key mismatch or corrupted data")
            raise EncryptionError("Invalid token: key mismatch or corrupted data") from exc
        except Exception as exc:
            logger.error(f"[ERROR] Decryption failed: {exc}")
            raise EncryptionError(f"Decryption failed: {exc}") from exc

    @staticmethod
    def mask(value: str, visible: int = 4) -> str:
        """Return a masked representation for UI display."""
        if not value:
            return ""
        if len(value) <= visible * 2:
            return "*" * len(value)
        return f"{value[:visible]}{'*' * 8}{value[-visible:]}"


vault = SecretVault(settings.MASTER_ENCRYPTION_KEY)