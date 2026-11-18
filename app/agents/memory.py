from sqlalchemy import select

from app.data.models import Message


class ConversationMemory:
    """DB-backed sliding-window memory, keyed by session_id."""

    def __init__(self, db, session_id: str, window: int = 10):
        self.db, self.session_id, self.window = db, session_id, window

    def add(self, role: str, content: str) -> None:
        self.db.add(Message(session_id=self.session_id, role=role, content=content))
        self.db.commit()

    def messages(self) -> list[Message]:
        rows = self.db.scalars(select(Message).where(Message.session_id == self.session_id)
                               .order_by(Message.id.desc()).limit(self.window)).all()
        return list(reversed(rows))

    def context(self) -> str:
        return "\n".join(f"{m.role}: {m.content}" for m in self.messages()) or "(none)"
