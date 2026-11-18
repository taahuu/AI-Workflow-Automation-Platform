from app.data.models import WorkflowRun
from app.domain.orchestrator import Orchestrator


def create_run(db, session_id: str, request: str) -> WorkflowRun:
    run = WorkflowRun(session_id=session_id, request=request, status="queued")
    db.add(run)
    db.commit()
    return run


def execute_run(db, run: WorkflowRun, orch: Orchestrator) -> WorkflowRun:
    run.status = "running"
    db.commit()
    try:
        res = orch.run(db, run.session_id, run.request)
        run.intent, run.answer, run.steps, run.status = res.intent, res.answer, res.steps, res.status
    except Exception as e:
        db.rollback()
        run.status, run.error = "failed", str(e)
    db.commit()
    return run
