from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def create_audit_log(
    *,
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
) -> AuditLog:
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    db.add(log)
    db.flush()

    return log
