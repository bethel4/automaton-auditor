# src/llm.py

import os
from langchain_openai import ChatOpenAI


def get_llm(model: str = "grok-2-latest"):
    return ChatOpenAI(
        model=model,
        temperature=0,
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )