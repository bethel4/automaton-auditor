# src/llm.py

import os
from typing import Optional
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

# Don't load at module level - use functions to get values when needed

def get_env_variable(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable, with option to reload if needed"""
    # Try to get from environment
    value = os.getenv(var_name)
    
    # If not found, try loading .env again (as fallback)
    if value is None:
        load_dotenv(override=True)
        value = os.getenv(var_name)
    
    return value or default

def get_detective_model() -> str:
    """Get detective model from environment"""
    model = get_env_variable("DETECTIVE_MODEL")
    if not model:
        print("⚠️ DETECTIVE_MODEL not set, using default: qwen2.5-coder:7b")
        return "qwen2.5-coder:7b"
    return model

def get_judge_model() -> str:
    """Get judge model from environment"""
    model = get_env_variable("JUDGE_MODEL")
    if not model:
        print("⚠️ JUDGE_MODEL not set, using default: deepseek-v3.1:671b-cloud")
        return "deepseek-v3.1:671b-cloud"
    return model

def get_vision_model() -> str:
    """Get vision model from environment"""
    model = get_env_variable("VISION_MODEL")
    if not model:
        print("⚠️ VISION_MODEL not set, using detective model as fallback")
        return get_detective_model()
    return model

def get_ollama_base_url() -> str:
    """Get Ollama base URL from environment"""
    url = get_env_variable("OLLAMA_BASE_URL", "http://localhost:11434")
    return url

def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.0,
    num_predict: Optional[int] = None,
    base_url: Optional[str] = None
):
    """Get Ollama LLM instance"""
    base_url = base_url or get_ollama_base_url()
    
    if model is None:
        raise ValueError("❌ No model specified! Check your .env file")
    
    print(f"🔄 Initializing Ollama with model: {model} at {base_url}")
    
    return ChatOllama(
        model=model,
        temperature=temperature,
        num_predict=num_predict,
        base_url=base_url,
        format="json"
    )

def get_detective_llm():
    """Get LLM for detective pattern recognition"""
    model = get_detective_model()
    print(f"🔍 Detective using model: {model}")
    return get_llm(model=model, temperature=0.0)

def get_judge_llm():
    """Get LLM for judge personas"""
    model = get_judge_model()
    print(f"⚖️ Judge using model: {model}")
    return get_llm(model=model, temperature=0.2)

def get_vision_llm():
    """Get multimodal LLM for vision tasks"""
    model = get_vision_model()
    print(f"👁️ Vision using model: {model}")
    return get_llm(model=model, temperature=0.0)

def get_fallback_llm():
    """Get fallback LLM when primary fails"""
    return get_detective_llm()