from fastapi import APIRouter, Depends, HTTPException

from app.agents.tools import AnalyzeDocument
from app.api.schemas import DocumentIn
from app.data.db import get_db
from app.data.models import Document

router = APIRouter(tags=["documents"])


@router.post("/documents", status_code=201)
def upload(body: DocumentIn, db=Depends(get_db)):
    d = Document(title=body.title, content=body.content)
    db.add(d)
    db.commit()
    return {"id": d.id, "title": d.title}


@router.post("/documents/{doc_id}/analyze")
def analyze(doc_id: int, db=Depends(get_db)):
    """Deterministic analysis pipeline (no LLM needed); result persisted on the document."""
    if db.get(Document, doc_id) is None:
        raise HTTPException(404, "document not found")
    return AnalyzeDocument().run(db, document_id=doc_id)
