"""End-to-end: HTTP API -> queue -> worker -> agent -> tools -> DB -> HTTP API."""
from app.infra.worker import process_next

CONTRACT = ("Supplier must deliver by 1 Dec. Payment should be made within 30 days. "
            "Late delivery triggers a penalty and the buyer may terminate.")


def _submit_and_work(client, db, session, msg):
    run = client.post("/api/v1/workflows/runs", json={"session_id": session, "message": msg})
    assert run.status_code == 202 and run.json()["status"] == "queued"
    assert process_next(db) is True
    return client.get(f"/api/v1/workflows/runs/{run.json()['run_id']}").json()


def test_e2e_document_analysis(client, db):
    doc = client.post("/api/v1/documents", json={"title": "Contract", "content": CONTRACT}).json()
    out = _submit_and_work(client, db, "e1", f"Analyze document {doc['id']}")
    assert out["status"] == "completed" and out["intent"] == "document_analysis"
    assert out["steps"][0]["output"]["risk_flags"] == ["penalty", "terminate"]


def test_e2e_recommendation_then_task_with_memory(client, db):
    rec = _submit_and_work(client, db, "e2", "Recommend what to reorder")
    assert rec["status"] == "completed" and "reorder 35 x SKU-100" in rec["answer"]
    task = _submit_and_work(client, db, "e2", "Create a task: Reorder SKU-100 assign to alice")
    assert task["status"] == "completed" and "prior messages" in task["answer"]
    tasks = client.get("/api/v1/tasks").json()
    assert tasks == [{"id": 1, "title": "Reorder SKU-100", "assignee": "alice", "status": "open"}]


def test_e2e_failure_path_is_recorded(client, db):
    out = _submit_and_work(client, db, "e3", "Analyze document 12345")
    assert out["status"] == "failed" and out["steps"][0]["status"] == "error"


def test_worker_idle_returns_false(db):
    assert process_next(db) is False
