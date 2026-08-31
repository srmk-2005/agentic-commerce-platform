"""API Router for Audit Logs."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import AuditLog
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get(
    "",
    response_model=List[AuditLogResponse],
    summary="Get chronological audit logs for a merchant",
)
@router.get(
    "/logs",
    response_model=List[AuditLogResponse],
    summary="Get chronological audit logs for a merchant",
)
def get_audit_logs(
    merchant_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if merchant_id:
        query = query.filter(AuditLog.merchant_id == merchant_id)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return logs
