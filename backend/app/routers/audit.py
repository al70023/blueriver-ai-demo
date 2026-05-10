from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def list_audit_logs(
    db: Session = Depends(get_db),
) -> list[dict[str, int | str | datetime | None]]:
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50).all()

    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "created_at": log.created_at,
        }
        for log in logs
    ]
