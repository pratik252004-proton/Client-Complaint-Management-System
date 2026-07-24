"""
A single-node LangGraph app (kept as a graph rather than a bare LLM call so
it's trivial to extend later with e.g. a retrieval node over SOPs/CAPA
history, or a routing node that decides between "answer directly" and
"look up complaint record"). Uses llama-3.3-70b-versatile for stronger
reasoning over open-ended QMS questions than the extraction model needs.
"""

from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END

from app.core.llm import get_chat_llm

SYSTEM_PROMPT = """You are the AI Complaint Intake Assistant embedded in a \
pharmaceutical API & FDF Quality Assurance Module. You help QA staff \
triage customer complaints in line with standard QMS practice (e.g. ICH \
Q10, 21 CFR 211.198 complaint handling). Be concise and precise. When \
relevant, note whether something looks like it may warrant a deviation, \
CAPA, or regulatory reportability review — but make clear you are a \
drafting aid, not a substitute for QA sign-off.

Current complaint record (may be partial):
{complaint_context}
"""


class ChatState(TypedDict, total=False):
    complaint_context: str
    history: List[dict]  # [{"role": "user"|"assistant", "content": str}, ...]
    user_message: str
    reply: str


def respond_node(state: ChatState) -> ChatState:
    llm = get_chat_llm()

    messages = [("system", SYSTEM_PROMPT.format(complaint_context=state.get("complaint_context") or "None yet."))]
    for turn in state.get("history", []):
        role = "human" if turn["role"] == "user" else "ai"
        messages.append((role, turn["content"]))
    messages.append(("human", state["user_message"]))

    response = llm.invoke(messages)
    state["reply"] = response.content
    return state


def build_chat_graph():
    graph = StateGraph(ChatState)
    graph.add_node("respond", respond_node)
    graph.set_entry_point("respond")
    graph.add_edge("respond", END)
    return graph.compile()


_chat_app = None


def get_chat_app():
    global _chat_app
    if _chat_app is None:
        _chat_app = build_chat_graph()
    return _chat_app


def run_chat(user_message: str, complaint_context: str = "", history: Optional[List[dict]] = None) -> str:
    app = get_chat_app()
    result: ChatState = app.invoke(
        {
            "user_message": user_message,
            "complaint_context": complaint_context,
            "history": history or [],
        }
    )
    return result["reply"]
