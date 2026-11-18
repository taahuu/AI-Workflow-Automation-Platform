"""Workflow routing: intent -> workflow definition with an allow-list of tools (guardrail)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowDef:
    intent: str
    allowed_tools: tuple[str, ...]


WORKFLOWS = {w.intent: w for w in [
    WorkflowDef("document_analysis", ("analyze_document",)),
    WorkflowDef("data_retrieval", ("query_orders", "get_inventory")),
    WorkflowDef("recommendation", ("get_inventory", "recommend_actions", "query_orders")),
    WorkflowDef("task_execution", ("create_task",)),
    WorkflowDef("general", ()),
]}


def route(intent: str) -> WorkflowDef:
    return WORKFLOWS.get(intent, WORKFLOWS["general"])
