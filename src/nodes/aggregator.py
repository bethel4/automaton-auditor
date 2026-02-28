# src/nodes/aggregator.py

from typing import Dict, Any
from langsmith import traceable
from src.state import AgentState


@traceable(name="evidence_aggregator", run_type="chain")
def evidence_aggregator(state: AgentState) -> Dict[str, Any]:
    """
    Aggregates evidence from all detectives.
    """
    evidences = state.get("evidences", {})
    errors = state.get("errors", [])
    
    print(f"\n{'='*60}")
    print("📊 EVIDENCE AGGREGATOR")
    print(f"{'='*60}")
    
    # Log what we received
    print(f"Received from detectives: {list(evidences.keys())}")
    
    # Detailed breakdown of evidence
    total_evidence = 0
    for detective, ev_list in evidences.items():
        print(f"\n📁 {detective}: {len(ev_list)} evidence items")
        for i, ev in enumerate(ev_list):
            print(f"  {i+1}. {ev.goal}")
            print(f"     Found: {ev.found}, Confidence: {ev.confidence}")
            total_evidence += 1
    
    print(f"\n📊 TOTAL EVIDENCE: {total_evidence} items")
    
    # Check for missing evidence
    required_detectives = ["repo_investigator", "doc_analyst", "vision_inspector"]
    missing = [d for d in required_detectives if d not in evidences]
    
    if missing:
        print(f"⚠️ Missing evidence from: {missing}")
        errors.append(f"Missing evidence from: {missing}")
    else:
        print("✅ All detectives provided evidence")
    
    print(f"{'='*60}\n")
    
    return {
        "evidences": evidences,
        "errors": errors
    }