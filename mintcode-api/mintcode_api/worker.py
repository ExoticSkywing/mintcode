from __future__ import annotations

import time
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from mintcode_api.config import settings
from mintcode_api.db import Base, SessionLocal, engine
from mintcode_api.models import RedeemTask


def _process_one(task: RedeemTask, db: Session) -> None:
    import secrets

    task.status = "PROCESSING"
    db.flush()

    if not task.result_code:
        task.result_code = str(secrets.randbelow(1_000_000)).zfill(6)

    task.status = "DONE"


def _claim_next(db: Session) -> Optional[RedeemTask]:
    for _ in range(5):
        task_id = db.execute(
            select(RedeemTask.id)
            .where(RedeemTask.status == "PENDING")
            .order_by(RedeemTask.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        if task_id is None:
            return None

        res = db.execute(
            update(RedeemTask)
            .where(RedeemTask.id == task_id)
            .where(RedeemTask.status == "PENDING")
            .values(status="PROCESSING")
        )
        if getattr(res, "rowcount", 0) == 1:
            db.flush()
            return db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    return None


def run_loop(poll_seconds: float = 1.0) -> None:
    Base.metadata.create_all(bind=engine)
    while True:
        db = SessionLocal()
        try:
            task = _claim_next(db)
            if task is None:
                db.commit()
                time.sleep(poll_seconds)
                continue

            try:
                _process_one(task, db)
                db.commit()
            except Exception:
                db.rollback()
                db2 = SessionLocal()
                try:
                    t2 = db2.execute(select(RedeemTask).where(RedeemTask.id == task.id).limit(1)).scalar_one_or_none()
                    if t2 is not None and t2.status in ("PENDING", "PROCESSING"):
                        t2.status = "FAILED"
                        db2.commit()
                finally:
                    db2.close()
        finally:
            db.close()


if __name__ == "__main__":
    _ = settings.database_url
    run_loop()
