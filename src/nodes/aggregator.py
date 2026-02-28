# src/nodes/aggregator.py

from typing import Dict, Any
from langsmith import traceable
from src.state import AgentState, Evidence


def _format_evidence_item(ev: Evidence, index: int) -> str:
    """Format a single Evidence as structured output."""
    content_preview = ""
    if ev.content is not None:
        if isinstance(ev.content, dict):
            content_preview = " | ".join(f"{k}={type(v).__name__}" for k, v in list(ev.content.items())[:5])
            if len(ev.content) > 5:
                content_preview += " ..."
        elif isinstance(ev.content, str):
            content_preview = ev.content[:120] + ("..." if len(ev.content) > 120 else "")
        else:
            content_preview = str(type(ev.content).__name__)
    lines = [
        f"  [{index}] Goal: {ev.goal}",
        f"      Found: {ev.found} | Confidence: {ev.confidence:.2f}",
        f"      Location: {ev.location}",
        f"      Rationale: {ev.rationale}",
    ]
    if content_preview:
        lines.append(f"      Content: {content_preview}")
    return "\n".join(lines)


@traceable(name="evidence_aggregator", run_type="chain")
def evidence_aggregator(state: AgentState) -> Dict[str, Any]:
    """
    Aggregates evidence from all detectives.
    """
    evidences = state.get("evidences", {})
    errors = state.get("errors", [])
    
    print(f"\n{'='*60}")
    print("📊 EVIDENCE AGGREGATOR — structured Evidence output")
    print(f"{'='*60}")
    
    print(f"Received from detectives: {list(evidences.keys())}\n")
    
    total_evidence = 0
    for detective, ev_list in evidences.items():
        print(f"📁 {detective}: {len(ev_list)} evidence items")
        for i, ev in enumerate(ev_list):
            print(_format_evidence_item(ev, i + 1))
            print()
            total_evidence += 1
    
    print(f"📊 TOTAL EVIDENCE: {total_evidence} items")
    
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