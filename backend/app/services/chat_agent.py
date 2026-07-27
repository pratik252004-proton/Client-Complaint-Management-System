"""
Conversational assistant agent — now with chat-driven form add/edit.

Graph: START -> parse_updates -> respond -> END

`parse_updates` (fast extraction model) checks whether the user's message
is asking to ADD or EDIT specific complaint fields (e.g. "add customer
name Acme Pharma", "change severity to Critical", "the batch number is
AMX-2026-0417") and returns only the fields explicitly mentioned, reusing
the same FIELD_SCHEMA as the document-extraction agent so both stay in
sync. If the message is just a question with no data to add/edit, it
returns an empty dict.

`respond` (larger reasoning model) generates the conversational reply,
aware of whether any fields were just updated so it can acknowledge them
naturally instead of ignoring what just happened.
"""

import json
import re
from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END

from app.core.llm import get_chat_llm, get_extraction_llm
from app.services.extraction_agent import FIELD_SCHEMA

UPDATE_PARSE_PROMPT = """You detect whether a chat message to a pharma QA \
complaint assistant is asking to ADD or EDIT specific complaint record \
fields (as opposed to just asking a question).

Only include a field if the user EXPLICITLY states a value for it in this \
message. Do not infer or guess values. If nothing is being added/edited, \
return an empty JSON object: {{}}

Return ONLY a JSON object using a subset of these keys (omit any not \
explicitly mentioned):
{field_schema}

Chat message:
\"\"\"
{user_message}
\"\"\"
"""

SYSTEM_PROMPT = """You are the AI Complaint Intake Assistant embedded in a \
pharmaceutical API & FDF Quality Assurance Module. You help QA staff \
triage customer complaints in line with standard QMS practice (e.g. ICH \
Q10, 21 CFR 211.198 complaint handling). Be concise and precise. When \
relevant, note whether something looks like it may warrant a deviation, \
CAPA, or regulatory reportability review — but make clear you are a \
drafting aid, not a substitute for QA sign-off.

If the "Fields just updated from this message" section below is non-empty, \
briefly confirm what you updated in your reply (e.g. "Got it — I've set \
the batch number to ..."). If it's empty, just answer normally.

Current complaint record (may be partial):
{complaint_context}

Fields just updated from this message:
{updated_fields}
"""


class ChatState(TypedDict, total=False):
    complaint_context: str
    history: List[dict]
    user_message: str
    reply: str
    form_updates: dict


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def parse_updates_node(state: ChatState) -> ChatState:
    llm = get_extraction_llm()
    field_schema_text = "\n".join(f"- {k}: {v}" for k, v in FIELD_SCHEMA.items())
    prompt = UPDATE_PARSE_PROMPT.format(
        field_schema=field_schema_text, user_message=state["user_message"]
    )
    response = llm.invoke(prompt)
    raw = _strip_json_fences(response.content)

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            data = {}
    except json.JSONDecodeError:
        data = {}

    # Drop anything not in the known schema and any null/empty values.
    cleaned = {k: v for k, v in data.items() if k in FIELD_SCHEMA and v not in (None, "")}
    state["form_updates"] = cleaned
    return state


def respond_node(state: ChatState) -> ChatState:
    llm = get_chat_llm()

    updated_fields = state.get("form_updates") or {}
    updated_fields_text = (
        "\n".join(f"- {k}: {v}" for k, v in updated_fields.items()) if updated_fields else "None"
    )

    messages = [
        (
            "system",
            SYSTEM_PROMPT.format(
                complaint_context=state.get("complaint_context") or "None yet.",
                updated_fields=updated_fields_text,
            ),
        )
    ]
    for turn in state.get("history", []):
        role = "human" if turn["role"] == "user" else "ai"
        messages.append((role, turn["content"]))
    messages.append(("human", state["user_message"]))

    response = llm.invoke(messages)
    state["reply"] = response.content
    return state


def build_chat_graph():
    graph = StateGraph(ChatState)
    graph.add_node("parse_updates", parse_updates_node)
    graph.add_node("respond", respond_node)
    graph.set_entry_point("parse_updates")
    graph.add_edge("parse_updates", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


_chat_app = None


def get_chat_app():
    global _chat_app
    if _chat_app is None:
        _chat_app = build_chat_graph()
    return _chat_app


def run_chat(
    user_message: str, complaint_context: str = "", history: Optional[List[dict]] = None
) -> dict:
    """Returns {"reply": str, "form_updates": dict} — form_updates is an
    empty dict when the message didn't ask to add/edit any fields."""
    app = get_chat_app()
    result: ChatState = app.invoke(
        {
            "user_message": user_message,
            "complaint_context": complaint_context,
            "history": history or [],
        }
    )
    return {"reply": result["reply"], "form_updates": result.get("form_updates", {})}
