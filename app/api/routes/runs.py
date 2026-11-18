from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.schemas import ChatIn, RunOut, run_out
from app.data.db import get_db
from app.data.models import Task, WorkflowRun
from app.domain.service import create_run

router = APIRouter(tags=["workflows"])


@router.post("/workflows/runs", response_model=RunOut, status_code=202)
def submit(body: ChatIn, db=Depends(get_db)):
    """Async path: enqueue; the worker executes. Poll GET /workflows/runs/{id}."""
    return run_out(create_run(db, body.session_id, body.message))


@router.get("/workflows/runs/{run_id}", response_model=RunOut)
def get_run(run_id: int, db=Depends(get_db)):
    r = db.get(WorkflowRun, run_id)
    if r is None:
        raise HTTPException(404, "run not found")
    return run_out(r)


@router.get("/tasks")
def tasks(db=Depends(get_db)):
    return [{"id": t.id, "title": t.title, "assignee": t.assignee, "status": t.status}
            for t in db.scalars(select(Task).order_by(Task.id))]
