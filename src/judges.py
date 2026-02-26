from src.state import JudicialOpinion, AgentState

def prosecutor(state: AgentState):
    # Evaluate security aspects of evidence
    opinion = JudicialOpinion(
        judge="Prosecutor",
        criterion_id="security",
        score=4,
        argument="Security risks identified in repo",
        cited_evidence=[ev.location for ev_list in state["evidences"].values() for ev in ev_list]
    )
    return {"opinions": [opinion]}

def defense(state: AgentState):
    opinion = JudicialOpinion(
        judge="Defense",
        criterion_id="effort",
        score=5,
        argument="Good effort and documentation",
        cited_evidence=[ev.location for ev_list in state["evidences"].values() for ev in ev_list]
    )
    return {"opinions": [opinion]}

def tech_lead(state: AgentState):
    opinion = JudicialOpinion(
        judge="TechLead",
        criterion_id="architecture",
        score=3,
        argument="Architecture needs improvements",
        cited_evidence=[ev.location for ev_list in state["evidences"].values() for ev in ev_list]
    )
    return {"opinions": [opinion]}