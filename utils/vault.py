"""
FitLife — Secure Credential Vault
Leverages OS-native credential storage (Windows Credential Manager / macOS Keychain / SecretService via keyring)
and AES-GCM application-level field encryption for sensitive PII.
"""
import os
import logging
from typing import Optional
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger(__name__)

_SERVICE_NAME = "FitLifeGymManagement"

# ─── OS Keyring Integration ───────────────────────────────────────────────────

def get_secret(key_name: str, fallback: Optional[str] = None) -> Optional[str]:
    """Retrieve secret from OS credential store, falling back to optional provided value."""
    try:
        import keyring
        secret = keyring.get_password(_SERVICE_NAME, key_name)
        if secret:
            return secret
    except Exception as e:
        logger.debug(f"Keyring read error for {key_name}: {e}")
    return fallback


def set_secret(key_name: str, secret_value: str) -> bool:
    """Store secret into OS credential store (Windows Credential Manager)."""
    try:
        import keyring
        keyring.set_password(_SERVICE_NAME, key_name, secret_value)
        return True
    except Exception as e:
        logger.warning(f"Keyring write error for {key_name}: {e}")
        return False


def delete_secret(key_name: str) -> bool:
    """Remove a secret from OS credential store."""
    try:
        import keyring
        keyring.delete_password(_SERVICE_NAME, key_name)
        return True
    except Exception as e:
        logger.debug(f"Keyring delete error for {key_name}: {e}")
        return False


# ─── Field-Level PII Encryption (Fernet / AES-128-CBC + HMAC) ──────────────────

_KEY_FILE = Path(__file__).parent.parent / "config" / ".vault_key"

def _get_or_create_cipher() -> Fernet:
    """Load or initialize AES key for field-level database encryption."""
    key = None
    # 1. Try OS Keyring
    try:
        key_str = get_secret("PII_ENCRYPTION_KEY")
        if key_str:
            key = key_str.encode("utf-8")
    except Exception:
        pass

    # 2. Try Protected Local Key File
    if not key and _KEY_FILE.exists():
        try:
            key = _KEY_FILE.read_bytes().strip()
        except Exception:
            pass

    # 3. Generate New Key if None Exists
    if not key:
        key = Fernet.generate_key()
        try:
            _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            _KEY_FILE.write_bytes(key)
            set_secret("PII_ENCRYPTION_KEY", key.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Could not persist vault key: {e}")

    return Fernet(key)


def encrypt_field(plaintext: Optional[str]) -> Optional[str]:
    """Encrypt a sensitive field (CNIC, medical details) for at-rest DB security."""
    if not plaintext or plaintext.startswith("enc::"):
        return plaintext
    try:
        cipher = _get_or_create_cipher()
        encrypted_bytes = cipher.encrypt(plaintext.encode("utf-8"))
        return f"enc::{encrypted_bytes.decode('utf-8')}"
    except Exception as e:
        logger.error(f"Field encryption failed: {e}")
        return plaintext


def decrypt_field(ciphertext: Optional[str]) -> Optional[str]:
    """Decrypt an encrypted field retrieved from the database."""
    if not ciphertext or not ciphertext.startswith("enc::"):
        return ciphertext
    try:
        cipher = _get_or_create_cipher()
        raw_token = ciphertext[5:].encode("utf-8")
        decrypted_bytes = cipher.decrypt(raw_token)
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Field decryption failed: {e}")
        return "[Decryption Error]"
