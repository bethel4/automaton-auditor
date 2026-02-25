# src/graph.py

from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.detectives import repo_investigator, doc_analyst


def evidence_aggregator(state: AgentState):
    # In interim, just pass state forward
    return state


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("RepoInvestigator", repo_investigator)
    builder.add_node("DocAnalyst", doc_analyst)
    builder.add_node("EvidenceAggregator", evidence_aggregator)

    # Fan-out
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")

    builder.set_entry_point("RepoInvestigator")
    builder.add_edge("EvidenceAggregator", END)

    return builder.compile()