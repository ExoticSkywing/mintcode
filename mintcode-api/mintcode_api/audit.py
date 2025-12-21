from __future__ import annotations

import datetime as dt
import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from mintcode_api.models import AuditLog


def add_audit_log(
    db: Session,
    *,
    actor_type: str,
    actor_id: str,
    ip: Optional[str],
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    row = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        ip=ip,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail_json=json.dumps(detail, ensure_ascii=False) if detail is not None else None,
        created_at=dt.datetime.utcnow(),
    )
    db.add(row)
