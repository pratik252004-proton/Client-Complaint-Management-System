"""
Phase 3 — AI extraction agent.

LangGraph state machine:

    START -> extract -> validate --(invalid & attempts left)--> extract
                            |
                            +--(valid OR out of attempts)--> finalize -> END

`extract` prompts the configured Groq extraction model (see
GROQ_EXTRACTION_MODEL in .env) for a JSON object matching the
complaint form schema. `validate` does light structural checking (required
keys, enum membership, date format) without another LLM call. `finalize`
normalizes values (severity/priority casing, date formatting) before
handing the result back to the FastAPI route.
"""

import json
import logging
import re
from datetime import datetime
from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END

from app.core.llm import get_extraction_llm

logger = logging.getLogger("uvicorn.error")

FIELD_SCHEMA = {
    "complaint_source": "string, e.g. Email, Phone, Customer Portal, Distributor Visit",
    "customer_name": "string, the customer or company name",
    "product_name": "string, the pharmaceutical product name",
    "product_strength": "string, e.g. '500mg Capsules' or '99.5% Purity'",
    "batch_lot_number": "string, the batch or lot number referenced",
    "manufacturing_date": "date in YYYY-MM-DD format, or null if not mentioned",
    "expiry_date": "date in YYYY-MM-DD format, or null if not mentioned",
    "quantity_affected": "number (no units), or null if not mentioned",
    "complaint_type": "string, e.g. Product Quality, Packaging Defect, Adverse Event, Documentation",
    "complaint_date": "date in YYYY-MM-DD format, the date the complaint was raised/received",
    "detailed_description": "string, a clear 2-4 sentence summary of the complaint",
    "initial_severity": "one of: Critical, Major, Minor",
    "priority": "one of: High, Medium, Low",
}

ALLOWED_SEVERITY = {"critical", "major", "minor"}
ALLOWED_PRIORITY = {"high", "medium", "low"}
MAX_ATTEMPTS = 2

SYSTEM_PROMPT = """You are a data-extraction assistant for a pharmaceutical \
Quality Assurance (QA) system that processes customer complaints for API \
(Active Pharmaceutical Ingredient) and FDF (Finished Dosage Form) products.

Extract the requested fields from the complaint text and return ONLY a \
single valid JSON object — no markdown fences, no commentary, no leading \
or trailing text, no explanation of your reasoning before or after the \
JSON. Your entire response must be parseable as JSON on its own. If a \
field is not mentioned, use null. Infer \
`initial_severity` and `priority` conservatively based on QMS norms: \
adverse events or sterility/identity failures are Critical/High; \
significant quality defects are Major/High or Major/Medium; cosmetic or \
minor packaging issues are Minor/Low or Minor/Medium.

Fields and formats:
{field_schema}
"""


class ExtractionState(TypedDict, total=False):
    raw_text: str
    structured_data: dict
    errors: List[str]
    attempts: int
    final: dict


def _build_prompt(state: ExtractionState) -> str:
    field_schema_text = "\n".join(f"- {k}: {v}" for k, v in FIELD_SCHEMA.items())
    prompt = SYSTEM_PROMPT.format(field_schema=field_schema_text)
    prompt += f"\n\nComplaint text:\n\"\"\"\n{state['raw_text']}\n\"\"\"\n"
    if state.get("errors"):
        prompt += (
            "\nYour previous attempt had these problems, fix them: "
            + "; ".join(state["errors"])
            + "\n"
        )
    return prompt


def _extract_json_object(text: str) -> Optional[dict]:
    """Robustly pull a JSON object out of an LLM response. Handles the
    plain case (response is pure JSON), the markdown-fenced case, and the
    "reasoning model" case where the model wraps the JSON in explanatory
    prose despite being told not to (common with gpt-oss-style models)."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: grab the outermost {...} block anywhere in the text.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def extract_node(state: ExtractionState) -> ExtractionState:
    llm = get_extraction_llm()
    prompt = _build_prompt(state)
    response = llm.invoke(prompt)

    data = _extract_json_object(response.content)
    if data is None:
        logger.warning(
            "Extraction model returned non-JSON-parseable output (attempt %s). Raw output: %.500s",
            state.get("attempts", 0) + 1,
            response.content,
        )
        data = {}
        state["errors"] = ["Output was not valid JSON."]

    state["structured_data"] = data
    state["attempts"] = state.get("attempts", 0) + 1
    return state


def validate_node(state: ExtractionState) -> ExtractionState:
    data = state.get("structured_data", {})
    errors = []

    for field in FIELD_SCHEMA:
        if field not in data:
            errors.append(f"Missing field '{field}'.")

    severity = str(data.get("initial_severity") or "").strip().lower()
    if severity and severity not in ALLOWED_SEVERITY:
        errors.append(f"'initial_severity' must be one of Critical/Major/Minor, got '{severity}'.")

    priority = str(data.get("priority") or "").strip().lower()
    if priority and priority not in ALLOWED_PRIORITY:
        errors.append(f"'priority' must be one of High/Medium/Low, got '{priority}'.")

    for date_field in ("manufacturing_date", "expiry_date", "complaint_date"):
        value = data.get(date_field)
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except (ValueError, TypeError):
                errors.append(f"'{date_field}' must be YYYY-MM-DD, got '{value}'.")

    state["errors"] = errors
    return state


def route_after_validate(state: ExtractionState) -> str:
    if not state.get("errors") or state.get("attempts", 0) >= MAX_ATTEMPTS:
        return "finalize"
    return "extract"


def finalize_node(state: ExtractionState) -> ExtractionState:
    data = dict(state.get("structured_data", {}))

    if data.get("initial_severity"):
        data["initial_severity"] = str(data["initial_severity"]).strip().capitalize()
    if data.get("priority"):
        data["priority"] = str(data["priority"]).strip().capitalize()

    # Drop anything that isn't part of the known schema to keep the
    # payload safe to feed straight into ComplaintCreate.
    state["final"] = {k: data.get(k) for k in FIELD_SCHEMA}
    return state


def build_extraction_graph():
    graph = StateGraph(ExtractionState)
    graph.add_node("extract", extract_node)
    graph.add_node("validate", validate_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "validate")
    graph.add_conditional_edges(
        "validate", route_after_validate, {"extract": "extract", "finalize": "finalize"}
    )
    graph.add_edge("finalize", END)

    return graph.compile()


_extraction_app = None


def get_extraction_app():
    global _extraction_app
    if _extraction_app is None:
        _extraction_app = build_extraction_graph()
    return _extraction_app


def run_extraction(raw_text: str) -> dict:
    app = get_extraction_app()
    result: ExtractionState = app.invoke({"raw_text": raw_text, "attempts": 0})
    return result["final"]