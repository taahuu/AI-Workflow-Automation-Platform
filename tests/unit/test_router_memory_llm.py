import pytest

from app.agents.llm import FakeLLM, parse_json
from app.agents.memory import ConversationMemory
from app.domain.router import route


@pytest.mark.parametrize("text,intent", [
    ("Please analyze document 1", "document_analysis"),
    ("Show me pending orders", "data_retrieval"),
    ("Recommend what to reorder", "recommendation"),
    ("Create a task: call vendor", "task_execution"),
    ("hello there", "general"),
])
def test_fake_classifier(text, intent):
    assert FakeLLM().classify(text, "(none)")["intent"] == intent


def test_route_unknown_falls_back_to_general():
    assert route("nonsense").intent == "general" and route("nonsense").allowed_tools == ()


def test_parse_json_handles_fences_and_garbage():
    assert parse_json('```json\n{"a": 1}\n```', None) == {"a": 1}
    assert parse_json("not json", []) == []


def test_memory_window_and_isolation(db):
    m = ConversationMemory(db, "s1", window=2)
    for i in range(4):
        m.add("user", f"m{i}")
    ConversationMemory(db, "s2").add("user", "other")
    assert [x.content for x in m.messages()] == ["m2", "m3"]
    assert "other" not in m.context()
