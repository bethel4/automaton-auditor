# src/llm.py

import os
from langchain_openai import ChatOpenAI


def get_llm(model: str = "grok-2-latest"):
    """Initialize LLM with LangSmith tracing enabled."""
    return ChatOpenAI(
        model=model,
        temperature=0,
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
        # LangSmith tracing is automatically enabled when LANGCHAIN_TRACING_V2=true
        # and LANGSMITH_API_KEY is set in environment variables
    )