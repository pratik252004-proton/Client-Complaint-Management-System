from langchain_groq import ChatGroq

from app.core.config import settings


def get_extraction_llm(temperature: float = 0.0) -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_extraction_model, 
        temperature=temperature,
    )


def get_chat_llm(temperature: float = 0.3) -> ChatGroq:
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_chat_model,  # llama-3.3-70b-versatile
        temperature=temperature,
    )
