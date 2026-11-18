from app.agents.llm import FakeLLM
from app.domain.orchestrator import Orchestrator


class EvilLLM(FakeLLM):
    def plan(self, *a, **k):  # tries a tool outside the workflow allow-list
        return [{"tool": "create_task", "args": {"title": "pwn"}}]

    def classify(self, *a, **k):
        return {"intent": "data_retrieval"}


def test_multi_step_recommendation(db):
    r = Orchestrator(FakeLLM()).run(db, "s", "Recommend what to reorder")
    assert r.status == "completed" and [s["tool"] for s in r.steps] == ["get_inventory", "recommend_actions"]
    assert "SKU-100" in r.answer


def test_guardrail_rejects_disallowed_tool(db):
    r = Orchestrator(EvilLLM()).run(db, "s", "show orders")
    assert r.status == "failed" and r.steps[0]["status"] == "rejected"


def test_tool_failure_is_reported_not_raised(db):
    r = Orchestrator(FakeLLM()).run(db, "s", "analyze document 404")
    assert r.status == "failed" and "not found" in r.answer


def test_memory_carries_across_turns(db):
    o = Orchestrator(FakeLLM())
    o.run(db, "s", "show pending orders")
    assert "prior messages" in o.run(db, "s", "show shipped orders").answer


def test_general_intent_no_tools(db):
    r = Orchestrator(FakeLLM()).run(db, "s", "hello")
    assert r.status == "completed" and r.steps == []
