import time
from dataclasses import dataclass, field

from app.agents.llm import LLM
from app.agents.memory import ConversationMemory
from app.agents.tools import ToolRegistry
from app.config import get_settings
from app.domain.router import route


@dataclass
class RunResult:
    intent: str
    status: str  # completed | partial | failed
    answer: str
    steps: list = field(default_factory=list)


class Orchestrator:
    """classify -> route -> plan -> validate -> execute tools -> summarize -> remember."""

    def __init__(self, llm: LLM, tools: ToolRegistry | None = None):
        self.llm, self.tools = llm, tools or ToolRegistry()
        self.settings = get_settings()

    def run(self, db, session_id: str, request: str) -> RunResult:
        memory = ConversationMemory(db, session_id, self.settings.memory_window)
        history = memory.context()
        memory.add("user", request)

        intent = self.llm.classify(request, history).get("intent", "general")
        wf = route(intent)
        plan = self.llm.plan(request, wf.intent, self.tools.catalog(wf.allowed_tools), history)
        steps = []
        for item in plan[: self.settings.max_agent_steps]:
            name, args = item.get("tool"), item.get("args", {})
            rec = {"tool": name, "args": args, "status": "ok", "output": None, "error": None, "ms": 0}
            if name not in wf.allowed_tools:
                rec.update(status="rejected", error=f"tool not allowed in workflow '{wf.intent}'")
            else:
                t0 = time.perf_counter()
                try:
                    rec["output"] = self.tools.execute(name, db, args)
                except Exception as e:  # tool failures are data, not crashes
                    db.rollback()
                    rec.update(status="error", error=str(e))
                rec["ms"] = int((time.perf_counter() - t0) * 1000)
            steps.append(rec)

        oks = [s["status"] == "ok" for s in steps]
        status = "completed" if all(oks) else ("partial" if any(oks) else "failed")
        answer = self.llm.summarize(request, wf.intent, steps, history)
        memory.add("assistant", answer)
        return RunResult(wf.intent, status, answer, steps)
