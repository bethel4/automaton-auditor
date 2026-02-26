# src/nodes/judges.py

import json
import os
from typing import Dict, List
from src.state import JudicialOpinion, AgentState, Evidence
from src.llm import get_llm

# Load rubric for judicial logic
with open('rubric.json', 'r') as f:
    rubric = json.load(f)

# Persona-specific system prompts
PROSECUTOR_PROMPT = """You are the PROSECUTOR in this Digital Courtroom. Your core philosophy: "Trust No One. Assume Vibe Coding."

Your mission: Scrutinize the evidence for gaps, security flaws, and laziness. Be harsh but fair.

Scoring guidelines:
- Look for bypassed structure and missing requirements
- Flag security vulnerabilities immediately
- If evidence shows linear pipeline instead of parallel execution, score 1
- If judges return freeform text instead of Pydantic models, charge "Hallucination Liability"
- Provide specific missing elements that justify low scores

You MUST return a JudicialOpinion with:
- score (1-5): Be critical, high standards
- argument: Specific technical criticisms with evidence citations
- cited_evidence: Reference specific evidence items that support your criticism

Be adversarial but professional. The truth depends on your scrutiny."""

DEFENSE_PROMPT = """You are the DEFENSE ATTORNEY in this Digital Courtroom. Your core philosophy: "Reward Effort and Intent. Look for the 'Spirit of the Law'."

Your mission: Highlight creative workarounds, deep thought, and effort, even if implementation is imperfect.

Scoring guidelines:
- Look for engineering process and iteration in git history
- Reward sophisticated logic even if syntax is imperfect
- If architecture is buggy but shows deep understanding, argue for higher scores
- Consider the "struggle and iteration" story told by commits
- Focus on intent and architectural vision

You MUST return a JudicialOpinion with:
- score (1-5): Be generous but realistic
- argument: Highlight strengths and creative solutions
- cited_evidence: Reference evidence that shows effort and intent

Be optimistic but grounded. Good engineering deserves recognition."""

TECH_LEAD_PROMPT = """You are the TECH LEAD in this Digital Courtroom. Your core philosophy: "Does it actually work? Is it maintainable?"

Your mission: Evaluate architectural soundness, code cleanliness, and practical viability.

Scoring guidelines:
- Focus on actual artifacts and implementation quality
- Check if reducers (operator.add, operator.ior) are properly used
- Evaluate if tool calls are isolated and safe
- Assess modularity and maintainability
- You are the tie-breaker between Prosecutor and Defense

You MUST return a JudicialOpinion with:
- score (1-5): Be pragmatic and realistic
- argument: Technical assessment with specific code analysis
- cited_evidence: Reference concrete technical evidence

Be practical and technical. Production quality is your standard."""

def prosecutor(state: AgentState) -> Dict:
    """Prosecutor judge node - adversarial analysis."""
    llm = get_llm()
    
    # Get relevant evidence for github_repo dimensions
    repo_evidences = []
    for evidence_list in state["evidences"].values():
        repo_evidences.extend(evidence_list)
    
    # Filter for relevant dimensions
    relevant_dimensions = [dim for dim in rubric['dimensions'] 
                          if dim['target_artifact'] == 'github_repo']
    
    opinions = []
    
    for dimension in relevant_dimensions:
        # Create evidence context
        evidence_text = "\n".join([
            f"- {ev.goal}: {ev.rationale} (confidence: {ev.confidence})"
            for ev in repo_evidences if ev.goal == dimension['name']
        ])
        
        prompt = f"""Evaluate this repository for the criterion: {dimension['name']}

Evidence:
{evidence_text}

Success Pattern: {dimension['success_pattern']}
Failure Pattern: {dimension['failure_pattern']}

{PROSECUTOR_PROMPT}"""
        
        try:
            structured_llm = llm.with_structured_output(JudicialOpinion)
            opinion = structured_llm.invoke(prompt)
            opinions.append(opinion)
        except Exception as e:
            # Fallback opinion
            opinion = JudicialOpinion(
                judge="Prosecutor",
                criterion_id=dimension['id'],
                score=2,
                argument=f"Prosecutor analysis failed: {str(e)}",
                cited_evidence=[]
            )
            opinions.append(opinion)
    
    return {"opinions": opinions}

def defense(state: AgentState) -> Dict:
    """Defense judge node - optimistic analysis."""
    llm = get_llm()
    
    # Get relevant evidence
    repo_evidences = []
    pdf_evidences = []
    for key, evidence_list in state["evidences"].items():
        if "repo" in key:
            repo_evidences.extend(evidence_list)
        elif "pdf" in key:
            pdf_evidences.extend(evidence_list)
    
    all_evidences = repo_evidences + pdf_evidences
    
    relevant_dimensions = rubric['dimensions']
    opinions = []
    
    for dimension in relevant_dimensions:
        # Create evidence context
        evidence_text = "\n".join([
            f"- {ev.goal}: {ev.rationale} (confidence: {ev.confidence})"
            for ev in all_evidences if ev.goal == dimension['name']
        ])
        
        prompt = f"""Evaluate this work for the criterion: {dimension['name']}

Evidence:
{evidence_text}

Success Pattern: {dimension['success_pattern']}
Failure Pattern: {dimension['failure_pattern']}

{DEFENSE_PROMPT}"""
        
        try:
            structured_llm = llm.with_structured_output(JudicialOpinion)
            opinion = structured_llm.invoke(prompt)
            opinions.append(opinion)
        except Exception as e:
            # Fallback opinion
            opinion = JudicialOpinion(
                judge="Defense",
                criterion_id=dimension['id'],
                score=3,
                argument=f"Defense analysis failed: {str(e)}",
                cited_evidence=[]
            )
            opinions.append(opinion)
    
    return {"opinions": opinions}

def tech_lead(state: AgentState) -> Dict:
    """Tech Lead judge node - pragmatic analysis."""
    llm = get_llm()
    
    # Get relevant evidence
    repo_evidences = []
    for evidence_list in state["evidences"].values():
        repo_evidences.extend(evidence_list)
    
    relevant_dimensions = [dim for dim in rubric['dimensions'] 
                          if dim['target_artifact'] == 'github_repo']
    
    opinions = []
    
    for dimension in relevant_dimensions:
        # Create evidence context
        evidence_text = "\n".join([
            f"- {ev.goal}: {ev.rationale} (confidence: {ev.confidence})"
            for ev in repo_evidences if ev.goal == dimension['name']
        ])
        
        prompt = f"""Evaluate this repository for the criterion: {dimension['name']}

Evidence:
{evidence_text}

Success Pattern: {dimension['success_pattern']}
Failure Pattern: {dimension['failure_pattern']}

{TECH_LEAD_PROMPT}"""
        
        try:
            structured_llm = llm.with_structured_output(JudicialOpinion)
            opinion = structured_llm.invoke(prompt)
            opinions.append(opinion)
        except Exception as e:
            # Fallback opinion
            opinion = JudicialOpinion(
                judge="TechLead",
                criterion_id=dimension['id'],
                score=3,
                argument=f"Tech Lead analysis failed: {str(e)}",
                cited_evidence=[]
            )
            opinions.append(opinion)
    
    return {"opinions": opinions}
