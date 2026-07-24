"""
Groq LLM client factory.

- gemma2-9b-it: fast/cheap model used for structured extraction (Phase 3
  extraction agent). Good enough for pulling fields out of a fairly
  templated complaint email/document.
- llama-3.3-70b-versatile: stronger model used for the conversational
  assistant, where the user asks free-form questions about a complaint and
  we want better reasoning over QMS context (severity/CAPA guidance, etc).
"""

from langchain_groq import ChatGroq

from app.core.config import settings


def get_extraction_llm(temperature: float = 0.0) -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_extraction_model,  # gemma2-9b-it
        temperature=temperature,
    )


def get_chat_llm(temperature: float = 0.3) -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_chat_model,  # llama-3.3-70b-versatile
        temperature=temperature,
    )
