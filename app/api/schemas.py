from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class RunOut(BaseModel):
    run_id: int
    session_id: str
    status: str
    intent: str | None = None
    answer: str | None = None
    steps: list | None = None
    error: str | None = None


class DocumentIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100_000)


def run_out(r) -> RunOut:
    return RunOut(run_id=r.id, session_id=r.session_id, status=r.status, intent=r.intent,
                  answer=r.answer, steps=r.steps, error=r.error)
