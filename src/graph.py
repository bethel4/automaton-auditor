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
    
    # IMPORTANT: Set entry point to route to ALL detectives in parallel
    # Method 1: Using a router node (recommended)
    def route_to_detectives(state):
        """Route to all detectives in parallel"""
        # This function just returns the list of nodes to run in parallel
        return ["repo_investigator", "doc_analyst", "vision_inspector"]
    
    workflow.add_conditional_edges(
        "__start__",  # Special node that represents graph start
        route_to_detectives,
        {
            "repo_investigator": "repo_investigator",
            "doc_analyst": "doc_analyst", 
            "vision_inspector": "vision_inspector"
        }
    )
    
    # Alternative Method 2: If your LangGraph version supports it
    # workflow.add_edge("__start__", "repo_investigator")
    # workflow.add_edge("__start__", "doc_analyst")
    # workflow.add_edge("__start__", "vision_inspector")
    
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