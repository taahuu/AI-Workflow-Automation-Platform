from sqlalchemy import select

from app.data import models
from app.data.db import Base, SessionLocal, engine


def init_db() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalars(select(models.Order).limit(1)).first():
            return
        db.add_all([
            models.InventoryItem(sku="SKU-100", name="Widget", stock=5, reorder_level=20),
            models.InventoryItem(sku="SKU-200", name="Gadget", stock=100, reorder_level=30),
            models.InventoryItem(sku="SKU-300", name="Gizmo", stock=12, reorder_level=25),
        ])
        rows = [("Acme", "SKU-100", 10, 250.0, "pending"), ("Beta", "SKU-200", 5, 99.5, "pending"),
                ("Cyan", "SKU-300", 2, 40.0, "pending"), ("Acme", "SKU-200", 1, 19.9, "shipped"),
                ("Delta", "SKU-100", 3, 75.0, "shipped"), ("Echo", "SKU-300", 4, 80.0, "cancelled")]
        db.add_all([models.Order(customer=c, sku=s, qty=q, amount=a, status=st) for c, s, q, a, st in rows])
        db.commit()
