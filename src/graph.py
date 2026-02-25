# src/graph.py

from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.detectives import repo_investigator, doc_analyst


def evidence_aggregator(state: AgentState):
    return state  # Combine evidence from all parallel nodes


def build_graph():
    builder = StateGraph(AgentState)

    # START node: simple pass-through entry point for fan-out
    def start_node(state: AgentState):
        return state

    builder.add_node("START", start_node)

    # Parallel detective nodes
    builder.add_node("RepoInvestigator", repo_investigator)
    builder.add_node("DocAnalyst", doc_analyst)

    # Fan-in aggregator
    builder.add_node("EvidenceAggregator", evidence_aggregator)

    # Fan-out from START to both detectives (they run in parallel)
    builder.add_edge("START", "RepoInvestigator")
    builder.add_edge("START", "DocAnalyst")

    # Fan-in: both detectives feed into EvidenceAggregator
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")

    # Optional: add conditional edges for failure handling
    # builder.add_conditional_edge("RepoInvestigator", "CloneErrorHandler", condition=...)
    # builder.add_conditional_edge("DocAnalyst", "PDFErrorNode", condition=...)

    # Set START as the entry point and finish at END after aggregation
    builder.set_entry_point("START")
    builder.add_edge("EvidenceAggregator", END)

    return builder.compile()