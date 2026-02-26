from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.detectives import repo_investigator, doc_analyst, vision_inspector
from src.nodes.judges import prosecutor, defense, tech_lead
from src.nodes.justice import chief_justice
import json

# Load rubric for graph initialization
with open('rubric.json', 'r') as f:
    rubric = json.load(f)

def initialize_state(state: AgentState) -> AgentState:
    """Initialize state with rubric dimensions."""
    if "rubric_dimensions" not in state or not state["rubric_dimensions"]:
        state["rubric_dimensions"] = rubric["dimensions"]
    return state

def evidence_aggregator(state: AgentState) -> AgentState:
    """Aggregate evidence from all detectives."""
    # Evidence is already aggregated by state reducers
    return state

def opinion_aggregator(state: AgentState) -> AgentState:
    """Aggregate opinions from all judges."""
    # Opinions are already aggregated by state reducers
    return state

def should_continue_to_judges(state: AgentState) -> str:
    """Check if we have enough evidence to proceed to judges."""
    total_evidences = sum(len(evidence_list) for evidence_list in state["evidences"].values())
    
    if total_evidences == 0:
        return "evidence_missing"
    
    # Check if we have evidence from at least 2 detectives
    detective_count = len([key for key in state["evidences"].keys() if "analysis" in key])
    if detective_count < 2:
        return "evidence_missing"
    
    return "proceed_to_judges"

def should_continue_to_justice(state: AgentState) -> str:
    """Check if we have opinions from all judges."""
    total_opinions = len(state["opinions"])
    
    # We expect opinions from 3 judges for multiple criteria
    expected_opinions = len(rubric["dimensions"]) * 3  # 3 judges per dimension
    
    if total_opinions < expected_opinions * 0.5:  # At least 50% of expected opinions
        return "opinions_missing"
    
    return "proceed_to_justice"

def build_graph():
    """Build the complete Digital Courtroom StateGraph."""
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("InitializeState", initialize_state)
    
    # Detective Layer (Parallel Fan-Out)
    builder.add_node("RepoInvestigator", repo_investigator)
    builder.add_node("DocAnalyst", doc_analyst)
    builder.add_node("VisionInspector", vision_inspector)
    
    # Evidence Aggregation (Fan-In)
    builder.add_node("EvidenceAggregator", evidence_aggregator)
    
    # Judicial Layer (Parallel Fan-Out)
    builder.add_node("Prosecutor", prosecutor)
    builder.add_node("Defense", defense)
    builder.add_node("TechLead", tech_lead)
    
    # Opinion Aggregation (Fan-In)
    builder.add_node("OpinionAggregator", opinion_aggregator)
    
    # Chief Justice (Final Synthesis)
    builder.add_node("ChiefJustice", chief_justice)
    
    # Define edges
    
    # Start -> Initialize
    builder.add_edge("__start__", "InitializeState")
    
    # Initialize -> Detectives (Parallel Fan-Out)
    builder.add_edge("InitializeState", "RepoInvestigator")
    builder.add_edge("InitializeState", "DocAnalyst")
    builder.add_edge("InitializeState", "VisionInspector")
    
    # Detectives -> Evidence Aggregator (Fan-In)
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")
    builder.add_edge("VisionInspector", "EvidenceAggregator")
    
    # Evidence Aggregator -> Conditional Check
    builder.add_conditional_edges(
        "EvidenceAggregator",
        should_continue_to_judges,
        {
            "proceed_to_judges": "Prosecutor",
            "evidence_missing": "ChiefJustice"  # Skip to final report if evidence missing
        }
    )
    
    # Evidence -> Judges (Parallel Fan-Out)
    builder.add_edge("EvidenceAggregator", "Prosecutor")
    builder.add_edge("EvidenceAggregator", "Defense")
    builder.add_edge("EvidenceAggregator", "TechLead")
    
    # Judges -> Opinion Aggregator (Fan-In)
    builder.add_edge("Prosecutor", "OpinionAggregator")
    builder.add_edge("Defense", "OpinionAggregator")
    builder.add_edge("TechLead", "OpinionAggregator")
    
    # Opinion Aggregator -> Conditional Check
    builder.add_conditional_edges(
        "OpinionAggregator",
        should_continue_to_justice,
        {
            "proceed_to_justice": "ChiefJustice",
            "opinions_missing": "ChiefJustice"  # Proceed anyway with what we have
        }
    )
    
    # Chief Justice -> END
    builder.add_edge("ChiefJustice", END)
    
    return builder.compile()