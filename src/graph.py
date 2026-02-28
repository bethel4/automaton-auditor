# src/graph.py

from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.detectives import (
    repo_investigator, 
    doc_analyst, 
    vision_inspector
)
from src.nodes.aggregator import evidence_aggregator
from src.nodes.judges import prosecutor, defense, tech_lead
from src.nodes.justice import chief_justice
from src.utils.rubric_loader import ContextBuilder, load_rubric

def create_graph():
    # Load rubric once
    rubric = load_rubric("rubric.json")
    context_builder = ContextBuilder(rubric)
    
    # Initialize graph
    workflow = StateGraph(AgentState)
    
    # Add ALL nodes
    workflow.add_node("repo_investigator", repo_investigator)
    workflow.add_node("doc_analyst", doc_analyst)
    workflow.add_node("vision_inspector", vision_inspector)
    workflow.add_node("aggregator", evidence_aggregator)
    workflow.add_node("prosecutor", prosecutor)
    workflow.add_node("defense", defense)
    workflow.add_node("tech_lead", tech_lead)
    workflow.add_node("chief_justice", chief_justice)
    
    # ✅ FIXED: True parallel execution using proper LangGraph syntax
    # LangGraph automatically runs nodes in parallel when they have no dependencies
    # Set entry point to trigger all detectives
    workflow.set_entry_point("repo_investigator")
    
    # Create parallel execution by removing dependencies between detectives
    # All detectives can run in parallel since they don't depend on each other
    # We'll use a special approach: create a starter node that fans out
    
    def start_all_detectives(state):
        """Kick off all detectives simultaneously"""
        print(f"\n{'='*60}")
        print("🔍 Detectives collecting evidence (showing structured Evidence output)")
        print(f"{'='*60}\n")
        return state
    
    workflow.add_node("start_all_detectives", start_all_detectives)
    workflow.set_entry_point("start_all_detectives")
    
    # Fan out to all detectives in parallel
    workflow.add_edge("start_all_detectives", "repo_investigator")
    workflow.add_edge("start_all_detectives", "doc_analyst")
    workflow.add_edge("start_all_detectives", "vision_inspector")
    
    # All detectives fan-in to aggregator
    workflow.add_edge("repo_investigator", "aggregator")
    workflow.add_edge("doc_analyst", "aggregator")
    workflow.add_edge("vision_inspector", "aggregator")
    
    # Aggregator fans-out to judges
    workflow.add_edge("aggregator", "prosecutor")
    workflow.add_edge("aggregator", "defense")
    workflow.add_edge("aggregator", "tech_lead")
    
    # Judges fan-in to chief justice
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")
    
    # Chief justice ends the graph
    workflow.add_edge("chief_justice", END)
    
    # Compile with config
    return workflow.compile()