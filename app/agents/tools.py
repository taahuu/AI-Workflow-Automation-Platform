"""Tool integrations. Tools never accept raw SQL: queries are parameterised ORM calls."""
import re
from collections import Counter

from sqlalchemy import select

from app.data.models import Document, InventoryItem, Order, Task

STOP = set("this that with from have will your there their about which shall would could into than then them these those".split())
ORDER_STATUSES = {"pending", "shipped", "cancelled"}


class ToolError(Exception):
    pass


class Tool:
    name = ""
    description = ""

    def run(self, db, **kw) -> dict:
        raise NotImplementedError


class AnalyzeDocument(Tool):
    name = "analyze_document"
    description = "args: document_id (int) or text (str). Returns keywords, action items, risk flags."

    def run(self, db, document_id=None, text=None):
        doc = None
        if document_id is not None:
            doc = db.get(Document, int(document_id))
            if doc is None:
                raise ToolError(f"document {document_id} not found")
            text = doc.content
        if not text or not text.strip():
            raise ToolError("no text to analyze")
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        kw = [w for w, _ in Counter(w for w in words if w not in STOP).most_common(5)]
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", text) if s.strip()]
        actions = [s for s in sentences if re.search(r"\b(must|should|deadline|action|todo|need to)\b", s, re.I)]
        risks = sorted({r for r in ("penalty", "terminate", "liability", "breach") if r in text.lower()})
        out = {"word_count": len(text.split()), "keywords": kw, "action_items": actions, "risk_flags": risks}
        if doc:
            doc.analysis = out
            db.commit()
        return out


class QueryOrders(Tool):
    name = "query_orders"
    description = "args: status (pending|shipped|cancelled, optional), sku (optional), limit (<=50)."

    def run(self, db, status=None, sku=None, limit=10):
        if status is not None and status not in ORDER_STATUSES:
            raise ToolError(f"invalid status {status!r}")
        q = select(Order)
        if status:
            q = q.where(Order.status == status)
        if sku:
            q = q.where(Order.sku == sku)
        rows = db.scalars(q.order_by(Order.id).limit(min(int(limit), 50))).all()
        return {"count": len(rows), "total_amount": round(sum(r.amount for r in rows), 2),
                "orders": [{"id": r.id, "customer": r.customer, "sku": r.sku, "qty": r.qty,
                            "status": r.status} for r in rows]}


def _inventory(db):
    return [{"sku": i.sku, "name": i.name, "stock": i.stock, "reorder_level": i.reorder_level,
             "low_stock": i.stock < i.reorder_level} for i in db.scalars(select(InventoryItem).order_by(InventoryItem.sku))]


class GetInventory(Tool):
    name = "get_inventory"
    description = "no args. Returns stock levels with low_stock flags."

    def run(self, db):
        items = _inventory(db)
        return {"items": items, "low_stock_count": sum(i["low_stock"] for i in items)}


class RecommendActions(Tool):
    name = "recommend_actions"
    description = "no args. Returns reorder recommendations for low-stock SKUs."

    def run(self, db):
        recs = [{"sku": i["sku"], "action": "reorder", "quantity": i["reorder_level"] * 2 - i["stock"],
                 "reason": f"stock {i['stock']} below reorder level {i['reorder_level']}"}
                for i in _inventory(db) if i["low_stock"]]
        return {"recommendations": recs}


class CreateTask(Tool):
    name = "create_task"
    description = "args: title (str, required), assignee (str, optional). Creates a task row."

    def run(self, db, title=None, assignee="unassigned"):
        if not title or not title.strip() or len(title) > 200:
            raise ToolError("title required (1-200 chars)")
        t = Task(title=title.strip(), assignee=assignee or "unassigned")
        db.add(t)
        db.commit()
        return {"task_id": t.id, "title": t.title, "assignee": t.assignee, "status": t.status}


class ToolRegistry:
    def __init__(self, tools=None):
        tools = tools or [AnalyzeDocument(), QueryOrders(), GetInventory(), RecommendActions(), CreateTask()]
        self._tools = {t.name: t for t in tools}

    def catalog(self, names) -> dict:
        return {n: self._tools[n].description for n in names if n in self._tools}

    def execute(self, name, db, args):
        tool = self._tools.get(name)
        if tool is None:
            raise ToolError(f"unknown tool {name!r}")
        if not isinstance(args, dict):
            raise ToolError("args must be an object")
        try:
            return tool.run(db, **args)
        except TypeError as e:
            raise ToolError(f"bad arguments: {e}") from e
