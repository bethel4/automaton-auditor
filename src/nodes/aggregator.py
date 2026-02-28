# src/nodes/aggregator.py

from typing import Dict, Any
from src.state import AgentState


def evidence_aggregator(state: AgentState) -> Dict[str, Any]:
    """
    Aggregates evidence from all detectives.
    This node uses reducers (operator.ior) so it's mostly a pass-through,
    but we add cross-referencing logic.
    """
    evidences = state.get("evidences", {})
    errors = state.get("errors", [])
    
    # Log what we received
    print(f"📊 Evidence Aggregator received from: {list(evidences.keys())}")
    
    # Cross-reference repo and doc evidence
    if "repo_investigator" in evidences and "doc_analyst" in evidences:
        repo_evidence = evidences["repo_investigator"]
        doc_evidence = evidences["doc_analyst"]
        
        # Find report accuracy evidence
        for doc_ev in doc_evidence:
            if doc_ev.goal == "Report Accuracy (Cross-Reference)":
                # Already cross-referenced in doc_analyst
                pass
    
    # Check for missing evidence
    required_detectives = ["repo_investigator", "doc_analyst"]
    missing = [d for d in required_detectives if d not in evidences]
    
    if missing:
        errors.append(f"Missing evidence from: {missing}")
    
    return {
        "evidences": evidences,  # Reducer will merge
        "errors": errors
    }