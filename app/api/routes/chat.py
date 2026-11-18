from fastapi import APIRouter, Depends

from app.api.deps import get_orchestrator
from app.api.schemas import ChatIn, RunOut, run_out
from app.data.db import get_db
from app.domain.service import create_run, execute_run

router = APIRouter(tags=["agent"])


@router.post("/agent/chat", response_model=RunOut)
def chat(body: ChatIn, db=Depends(get_db)):
    """Synchronous agent call (low-latency path)."""
    run = create_run(db, body.session_id, body.message)
    return run_out(execute_run(db, run, get_orchestrator()))
