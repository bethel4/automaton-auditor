# src/llm_router.py

import os
import json
from typing import Optional, Any
from src.llm import get_detective_llm, get_judge_llm, get_vision_llm, get_fallback_llm

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


def get_llm_for_task(task_type: str):
    """
    Get appropriate LLM for task type
    
    Args:
        task_type: "detective", "judge", "vision", "synthesis"
    """
    if DEBUG_MODE:
        return MockLLM()
    
    if task_type == "vision":
        return get_vision_llm()
    elif task_type == "judge" or task_type == "synthesis":
        # Judges and synthesis need more capability
        return get_judge_llm()
    elif task_type == "detective":
        # Detectives just need pattern recognition
        return get_detective_llm()
    else:
        return get_detective_llm()


def mock_judicial_opinion(criterion_id: str, judge_type: str) -> Optional[Any]:
    """Return mock opinion in debug mode"""
    if not DEBUG_MODE:
        return None
    
    from src.state import JudicialOpinion
    
    # Return consistent mock opinions for testing
    mock_scores = {
        "git_forensic_analysis": {"Prosecutor": 2, "Defense": 4, "TechLead": 3},
        "state_management_rigor": {"Prosecutor": 3, "Defense": 4, "TechLead": 3},
        "graph_orchestration": {"Prosecutor": 1, "Defense": 3, "TechLead": 2},
        "safe_tool_engineering": {"Prosecutor": 2, "Defense": 4, "TechLead": 3},
        "structured_output_enforcement": {"Prosecutor": 3, "Defense": 4, "TechLead": 3},
        "judicial_nuance": {"Prosecutor": 2, "Defense": 4, "TechLead": 3},
        "chief_justice_synthesis": {"Prosecutor": 3, "Defense": 4, "TechLead": 3},
        "theoretical_depth": {"Prosecutor": 3, "Defense": 4, "TechLead": 3},
        "report_accuracy": {"Prosecutor": 3, "Defense": 4, "TechLead": 3},
        "swarm_visual": {"Prosecutor": 2, "Defense": 3, "TechLead": 2},
    }
    
    score = mock_scores.get(criterion_id, {}).get(judge_type, 3)
    
    return JudicialOpinion(
        judge=judge_type,
        criterion_id=criterion_id,
        score=score,
        argument=f"Mock {judge_type} opinion for {criterion_id}",
        cited_evidence=["mock_evidence"]
    )


class MockLLM:
    """Mock LLM for testing without API calls"""
    
    def invoke(self, prompt: str) -> Any:
        class MockResponse:
            def __init__(self):
                self.content = json.dumps({
                    "pattern_type": "iterative",
                    "understanding_level": "moderate",
                    "confidence": 0.8,
                    "rationale": "Mock analysis"
                })
        
        return MockResponse()
    
    def with_structured_output(self, schema):
        return self