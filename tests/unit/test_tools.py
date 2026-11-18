import pytest

from app.agents.tools import ToolError, ToolRegistry

reg = ToolRegistry()


def test_query_orders_pending(db):
    out = reg.execute("query_orders", db, {"status": "pending"})
    assert out["count"] == 3 and out["total_amount"] == 389.5


def test_query_orders_rejects_bad_status(db):
    with pytest.raises(ToolError):
        reg.execute("query_orders", db, {"status": "'; DROP TABLE orders;--"})


def test_inventory_low_stock(db):
    assert reg.execute("get_inventory", db, {})["low_stock_count"] == 2


def test_recommend_actions(db):
    recs = reg.execute("recommend_actions", db, {})["recommendations"]
    assert {r["sku"]: r["quantity"] for r in recs} == {"SKU-100": 35, "SKU-300": 38}


def test_analyze_text_flags_risk(db):
    out = reg.execute("analyze_document", db, {"text": "Vendor must deliver by Friday. Late delivery incurs a penalty."})
    assert out["risk_flags"] == ["penalty"] and len(out["action_items"]) == 1


def test_analyze_missing_document(db):
    with pytest.raises(ToolError):
        reg.execute("analyze_document", db, {"document_id": 999})


def test_create_task_validation(db):
    with pytest.raises(ToolError):
        reg.execute("create_task", db, {"title": "  "})
    assert reg.execute("create_task", db, {"title": "Call vendor"})["task_id"] == 1


def test_unknown_tool_and_bad_args(db):
    with pytest.raises(ToolError):
        reg.execute("rm_rf", db, {})
    with pytest.raises(ToolError):
        reg.execute("get_inventory", db, {"bogus": 1})
