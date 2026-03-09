"""Шифрование персональных данных (ФЗ-152).

Используется Fernet (AES-128-CBC + HMAC-SHA256) для шифрования
паспортных данных в БД. Ключ хранится в .env (PII_ENCRYPTION_KEY).

Генерация ключа:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet | None:
    global _fernet
    if _fernet is not None:
        return _fernet
    key = settings.PII_ENCRYPTION_KEY
    if not key:
        logger.warning("PII_ENCRYPTION_KEY not set — passport data stored unencrypted")
        return None
    _fernet = Fernet(key.encode())
    return _fernet


def encrypt_pii(value: str | None) -> str | None:
    """Зашифровать строку. Если ключ не настроен — возвращает как есть."""
    if value is None:
        return None
    f = _get_fernet()
    if f is None:
        return value
    return f.encrypt(value.encode()).decode()


def decrypt_pii(value: str | None) -> str | None:
    """Расшифровать строку. Если значение не зашифровано — возвращает как есть."""
    if value is None:
        return None
    f = _get_fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except (InvalidToken, Exception):
        # Значение не зашифровано (например, старые данные до миграции) — возвращаем как есть
        return value
