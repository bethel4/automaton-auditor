# src/llm.py

import os
from typing import Optional
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

# Get Ollama base URL from environment
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.0,
    num_predict: Optional[int] = None,
    base_url: Optional[str] = None
):
    """Get Ollama LLM instance"""
    base_url = base_url or OLLAMA_BASE_URL
    
    if model is None:
        raise ValueError("❌ No model specified!")
    
    print(f"🔄 Initializing Ollama with model: {model} at {base_url}")
    
    # Some models need format='json' to work properly
    return ChatOllama(
        model=model,
        temperature=temperature,
        num_predict=num_predict or 2048,  # Increase token limit
        base_url=base_url,
        format="json"  # This forces JSON mode if supported
    )

def get_detective_llm():
    """Get LLM for detective pattern recognition (faster model)"""
    model = os.getenv("DETECTIVE_MODEL", "qwen2.5-coder:7b")
    return get_llm(model=model, temperature=0.0)


def get_judge_llm():
    """Get LLM for judge personas (more capable model)"""
    model = os.getenv("JUDGE_MODEL", "deepseek-v3.1:671b-cloud")
    return get_llm(model=model, temperature=0.2)


def get_vision_llm():
    """Get multimodal LLM for vision tasks (if available)"""
    # Check if a vision model is configured, otherwise fallback to detective model
    vision_model = os.getenv("VISION_MODEL", "qwen2.5-coder:7b")
    try:
        return get_llm(model=vision_model, temperature=0.0)
    except:
        return get_detective_llm()


def get_fallback_llm():
    """Get fallback LLM when primary fails"""
    return get_detective_llm()