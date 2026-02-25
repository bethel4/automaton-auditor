# src/graph.py

from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.detectives import repo_investigator, doc_analyst


def evidence_aggregator(state: AgentState):
    return state  # Combine evidence from all parallel nodes


def build_graph():
    builder = StateGraph(AgentState)

    # Parallel detective nodes
    builder.add_node("RepoInvestigator", repo_investigator)
    builder.add_node("DocAnalyst", doc_analyst)

    # Fan-in aggregator
    builder.add_node("EvidenceAggregator", evidence_aggregator)

    # Parallel edges → fan-in
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")

    # Optional: add conditional edges for failure handling
    # builder.add_conditional_edge("RepoInvestigator", "CloneErrorHandler", condition=...)
    # builder.add_conditional_edge("DocAnalyst", "PDFErrorNode", condition=...)

    # Entry point and end
    builder.set_entry_point("RepoInvestigator")  # Or a new root node if needed
    builder.add_edge("EvidenceAggregator", END)

    return builder.compile()