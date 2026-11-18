def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_chat_validation(client):
    assert client.post("/api/v1/agent/chat", json={"session_id": "", "message": "x"}).status_code == 422
    assert client.post("/api/v1/agent/chat", json={"session_id": "a"}).status_code == 422


def test_chat_data_retrieval(client):
    r = client.post("/api/v1/agent/chat", json={"session_id": "a", "message": "show pending orders"})
    assert r.status_code == 200 and r.json()["intent"] == "data_retrieval"
    assert r.json()["steps"][0]["output"]["count"] == 3


def test_document_upload_and_analyze(client):
    d = client.post("/api/v1/documents", json={"title": "NDA", "content": "Party must sign. Breach allows termination."})
    assert d.status_code == 201
    out = client.post(f"/api/v1/documents/{d.json()['id']}/analyze").json()
    assert out["risk_flags"] == ["breach"]
    assert client.post("/api/v1/documents/999/analyze").status_code == 404


def test_run_404(client):
    assert client.get("/api/v1/workflows/runs/999").status_code == 404
