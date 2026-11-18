from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.data.db import get_db

router = APIRouter()


@router.get("/health")
def health(db=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
