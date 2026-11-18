"""Poll-based worker using the DB as queue (SKIP LOCKED on Postgres). Swap for Celery/SQS in phase 3."""
import logging
import time

from sqlalchemy import select

from app.api.deps import get_orchestrator
from app.data.db import SessionLocal
from app.data.models import WorkflowRun
from app.data.seed import init_db
from app.domain.service import execute_run

log = logging.getLogger("worker")


def process_next(db, orch=None) -> bool:
    run = db.scalars(select(WorkflowRun).where(WorkflowRun.status == "queued")
                     .order_by(WorkflowRun.id).limit(1).with_for_update(skip_locked=True)).first()
    if run is None:
        return False
    execute_run(db, run, orch or get_orchestrator())
    return True


def main(poll: float = 1.0):
    logging.basicConfig(level=logging.INFO)
    init_db()
    log.info("worker started")
    while True:
        with SessionLocal() as db:
            if not process_next(db):
                time.sleep(poll)


if __name__ == "__main__":
    main()
