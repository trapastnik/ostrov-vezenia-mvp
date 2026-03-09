"""Сервис записи аудит-лога действий администраторов."""
import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: str | uuid.UUID | None = None,
    operator_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Записать действие в аудит-лог (не блокирует основной процесс)."""
    try:
        entry = AuditLog(
            operator_id=operator_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            ip_address=ip_address,
        )
        db.add(entry)
        # НЕ делаем commit — коммит произойдёт вместе с основной транзакцией
    except Exception:
        logger.exception("Failed to write audit log: %s %s/%s", action, resource_type, resource_id)
