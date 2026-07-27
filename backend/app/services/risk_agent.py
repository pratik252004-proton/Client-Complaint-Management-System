"""
Addon — AI risk assessment agent.

Single-node LangGraph app that takes a complaint's current field values and
returns a structured risk summary: risk level, rationale, key concerns, and
recommended next actions. Uses the larger chat model since this needs
judgment/reasoning, not just extraction.
"""

from typing import TypedDict, Optional
import json
import re

from langgraph.graph import StateGraph, END

from app.core.llm import get_chat_llm

RISK_SYSTEM_PROMPT = """You are a QA risk-assessment aid embedded in a \
pharmaceutical API & FDF Quality Assurance Module. Given the complaint \
details below, produce a structured risk assessment.

Return ONLY a valid JSON object, no markdown fences, no commentary, with \
this exact shape:
{{
  "risk_level": "Critical" | "High" | "Medium" | "Low",
  "summary": "2-3 sentence plain-language summary of the risk",
  "key_concerns": ["short bullet", "short bullet", ...],
  "recommended_actions": ["short bullet", "short bullet", ...],
  "regulatory_flag": true | false
}}

Set "regulatory_flag" to true only if this plausibly warrants regulatory \
reportability review (e.g. adverse events, sterility/identity failures, \
potential recalls). Be conservative and evidence-based — base your \
assessment only on the details provided, and note if key information is \
missing rather than assuming it.

Complaint details:
{complaint_details}
"""


class RiskState(TypedDict, total=False):
    complaint_details: str
    result: dict


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def assess_node(state: RiskState) -> RiskState:
    llm = get_chat_llm(temperature=0.1)
    prompt = RISK_SYSTEM_PROMPT.format(complaint_details=state["complaint_details"])
    response = llm.invoke(prompt)
    raw = _strip_json_fences(response.content)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "risk_level": "Unknown",
            "summary": "Could not generate a structured risk assessment from the model output.",
            "key_concerns": [],
            "recommended_actions": [],
            "regulatory_flag": False,
        }

    state["result"] = data
    return state


def build_risk_graph():
    graph = StateGraph(RiskState)
    graph.add_node("assess", assess_node)
    graph.set_entry_point("assess")
    graph.add_edge("assess", END)
    return graph.compile()


_risk_app = None


def get_risk_app():
    global _risk_app
    if _risk_app is None:
        _risk_app = build_risk_graph()
    return _risk_app


def run_risk_assessment(complaint_fields: dict) -> dict:
    """complaint_fields: dict of the complaint's current field values
    (e.g. product_name, batch_lot_number, complaint_type, description,
    initial_severity, priority, quantity_affected, etc.)"""
    details_lines = [f"{k}: {v}" for k, v in complaint_fields.items() if v]
    complaint_details = "\n".join(details_lines) or "No details provided."

    app = get_risk_app()
    result: RiskState = app.invoke({"complaint_details": complaint_details})
    return result["result"]
