"""LLM abstraction: FakeLLM (deterministic, offline, used in tests) and OpenAILLM (LangChain)."""
import json
import re
from typing import Protocol

from app.agents import prompts
from app.config import get_settings

INTENTS = ["document_analysis", "data_retrieval", "recommendation", "task_execution", "general"]


class LLM(Protocol):
    def classify(self, request: str, history: str) -> dict: ...
    def plan(self, request: str, intent: str, tools: dict, history: str) -> list: ...
    def summarize(self, request: str, intent: str, steps: list, history: str) -> str: ...


def parse_json(text: str, default):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"[\[{].*[\]}]", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return default


class FakeLLM:
    def classify(self, request, history):
        r = request.lower()
        if re.search(r"\b(create|add|open)\b.*\btask\b|\bremind\b|\bassign\b", r):
            intent = "task_execution"
        elif re.search(r"document|analy[sz]e|contract|summari[sz]e", r):
            intent = "document_analysis"
        elif re.search(r"recommend|reorder|suggest|restock", r):
            intent = "recommendation"
        elif re.search(r"\border|orders|show|list|fetch|inventory|stock", r):
            intent = "data_retrieval"
        else:
            intent = "general"
        return {"intent": intent, "confidence": 0.9 if intent != "general" else 0.5}

    def plan(self, request, intent, tools, history):
        r = request.lower()
        if intent == "document_analysis":
            m = re.search(r"document\s*#?(\d+)", r)
            return [{"tool": "analyze_document",
                     "args": {"document_id": int(m.group(1))} if m else {"text": request}}]
        if intent == "data_retrieval":
            if "inventory" in r or "stock" in r:
                return [{"tool": "get_inventory", "args": {}}]
            m = re.search(r"pending|shipped|cancelled", r)
            return [{"tool": "query_orders", "args": {"status": m.group(0)} if m else {}}]
        if intent == "recommendation":
            return [{"tool": "get_inventory", "args": {}}, {"tool": "recommend_actions", "args": {}}]
        if intent == "task_execution":
            a = re.search(r"assign(?:ed)?\s+to\s+(\w+)", request, re.I)
            title = re.sub(r"\s*assign(?:ed)?\s+to\s+\w+", "", request, flags=re.I)
            title = title.split(":", 1)[1].strip() if ":" in title else title.strip()
            return [{"tool": "create_task", "args": {"title": title, "assignee": a.group(1) if a else "unassigned"}}]
        return []

    def summarize(self, request, intent, steps, history):
        parts = [f"[{intent}]"]
        if history not in ("", "(none)"):
            parts.append(f"(used {len(history.splitlines())} prior messages as context)")
        for s in steps:
            if s["status"] != "ok":
                parts.append(f"Step {s['tool']} {s['status']}: {s['error']}")
                continue
            o = s["output"]
            if s["tool"] == "analyze_document":
                parts.append(f"Document analyzed: {o['word_count']} words, keywords {o['keywords']}, "
                             f"{len(o['action_items'])} action item(s), risks {o['risk_flags']}.")
            elif s["tool"] == "query_orders":
                parts.append(f"Found {o['count']} order(s) totalling {o['total_amount']}.")
            elif s["tool"] == "get_inventory":
                parts.append(f"Inventory: {len(o['items'])} SKUs, {o['low_stock_count']} low on stock.")
            elif s["tool"] == "recommend_actions":
                parts.append("Recommendations: " + "; ".join(
                    f"reorder {r['quantity']} x {r['sku']}" for r in o["recommendations"]) + ".")
            elif s["tool"] == "create_task":
                parts.append(f"Task #{o['task_id']} created for {o['assignee']}: {o['title']}.")
        if not steps:
            parts.append("I can help with documents, orders, inventory recommendations and tasks.")
        return " ".join(parts)


class OpenAILLM:
    def __init__(self):
        from langchain_core.prompts import ChatPromptTemplate  # lazy: optional at test time
        from langchain_openai import ChatOpenAI
        self._tpl = ChatPromptTemplate
        self.model = ChatOpenAI(model=get_settings().openai_model, temperature=0, timeout=30, max_retries=2)

    def _call(self, template: str, **vars) -> str:
        chain = self._tpl.from_messages([("system", prompts.SYSTEM), ("human", template)]) | self.model
        return chain.invoke(vars).content

    def classify(self, request, history):
        out = parse_json(self._call(prompts.CLASSIFY, request=request, history=history), {})
        if not isinstance(out, dict) or out.get("intent") not in INTENTS:
            return {"intent": "general", "confidence": 0.0}
        return out

    def plan(self, request, intent, tools, history):
        t = "\n".join(f"- {k}: {v}" for k, v in tools.items()) or "(none)"
        out = parse_json(self._call(prompts.PLAN, request=request, intent=intent, tools=t, history=history), [])
        return [s for s in out if isinstance(s, dict)] if isinstance(out, list) else []

    def summarize(self, request, intent, steps, history):
        return self._call(prompts.SUMMARIZE, request=request, intent=intent, history=history,
                          results=json.dumps(steps, default=str)[:8000])


def get_llm() -> LLM:
    return OpenAILLM() if get_settings().llm_provider == "openai" else FakeLLM()
