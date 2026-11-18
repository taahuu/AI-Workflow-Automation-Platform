"""Versioned prompt templates. Literal braces are doubled for LangChain."""
PROMPT_VERSION = "v1"

SYSTEM = ("You are a business-operations assistant inside a workflow platform. "
          "Follow instructions exactly. When asked for JSON, return ONLY valid JSON.")

CLASSIFY = """Classify the user request into exactly one intent:
document_analysis | data_retrieval | recommendation | task_execution | general

Conversation so far:
{history}

Request: {request}

Return JSON: {{"intent": "<intent>", "confidence": <0-1>}}"""

PLAN = """Intent: {intent}
Available tools (use ONLY these):
{tools}

Conversation so far:
{history}

Request: {request}

Return a JSON list of ordered steps: [{{"tool": "<name>", "args": {{...}}}}].
Return [] if no tool is needed."""

SUMMARIZE = """Write a concise, factual answer for the user using ONLY the tool results.
If a step failed, say so plainly. Do not invent data.

Conversation so far:
{history}

Request: {request}
Intent: {intent}
Tool results (JSON): {results}"""
