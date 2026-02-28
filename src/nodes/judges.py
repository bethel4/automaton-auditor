# src/nodes/judges.py

import json
from typing import Dict, List, Any
from src.state import AgentState, JudicialOpinion, Evidence
from src.llm_router import get_llm_for_task, get_fallback_llm, mock_judicial_opinion, DEBUG_MODE

# Persona-specific system prompts
PROSECUTOR_PROMPT = """You are the PROSECUTOR in this Digital Courtroom. 
Your core philosophy: "Trust No One. Assume Vibe Coding."

Your mission: Scrutinize the evidence for gaps, security flaws, and laziness. 
Be harsh but factual. Look for what's MISSING.

Scoring guidelines (1-5):
1 - Complete failure, missing core requirements
2 - Significant gaps, multiple missing elements
3 - Adequate but with notable issues
4 - Good implementation with minor issues
5 - Excellent, no issues found

You MUST base your score on the EVIDENCE provided, not assumptions.
Cite specific evidence in your argument.

Return a JudicialOpinion with:
- score (1-5): Be critical, high standards
- argument: Specific technical criticisms with evidence citations
- cited_evidence: List of evidence goals you're referencing
"""

DEFENSE_PROMPT = """You are the DEFENSE ATTORNEY in this Digital Courtroom. 
Your core philosophy: "Reward Effort and Intent. Look for the 'Spirit of the Law'."

Your mission: Highlight creative workarounds, deep thought, and effort, 
even if implementation is imperfect.

Scoring guidelines (1-5):
1 - No effort shown, completely missing
2 - Attempted but fundamentally broken
3 - Good effort with working core concepts
4 - Solid implementation with creative solutions
5 - Exceptional work exceeding requirements

You MUST base your score on the EVIDENCE provided, not assumptions.
Cite specific evidence in your argument.

Return a JudicialOpinion with:
- score (1-5): Be generous but realistic
- argument: Highlight strengths and creative solutions
- cited_evidence: List of evidence goals you're referencing
"""

TECH_LEAD_PROMPT = """You are the TECH LEAD in this Digital Courtroom. 
Your core philosophy: "Does it actually work? Is it maintainable?"

Your mission: Evaluate architectural soundness, code cleanliness, and practical viability.

Scoring guidelines (1-5):
1 - Unusable, fundamentally broken
2 - Works but has major architectural issues
3 - Functional with some technical debt
4 - Solid architecture, production-ready
5 - Exemplary design, best practices followed

You MUST base your score on the EVIDENCE provided, not assumptions.
Cite specific evidence in your argument.

Return a JudicialOpinion with:
- score (1-5): Be pragmatic and realistic
- argument: Technical assessment with specific code analysis
- cited_evidence: List of evidence goals you're referencing
"""


def create_judge_node(judge_type: str):
    """
    Factory function to create judge nodes with proper persona
    
    Args:
        judge_type: "Prosecutor", "Defense", or "TechLead"
    """
    
    def judge_node(state: AgentState) -> Dict[str, Any]:
        """Judge node that evaluates evidence through persona lens"""
        
        # Select prompt based on judge type
        if judge_type == "Prosecutor":
            system_prompt = PROSECUTOR_PROMPT
        elif judge_type == "Defense":
            system_prompt = DEFENSE_PROMPT
        else:  # TechLead
            system_prompt = TECH_LEAD_PROMPT
        
        # Get rubric from config
        rubric_loader = state["config"]["rubric"]
        
        # Format all criteria for judges
        criteria_text = rubric_loader.format_criteria_for_judges()
        
        # Get all evidence
        all_evidence = []
        evidence_by_goal = {}
        
        for detective_name, evidence_list in state.get("evidences", {}).items():
            for evidence in evidence_list:
                all_evidence.append(evidence)
                if evidence.goal not in evidence_by_goal:
                    evidence_by_goal[evidence.goal] = []
                evidence_by_goal[evidence.goal].append(evidence)
        
        # Format evidence for prompt
        evidence_text = ""
        for goal, ev_list in evidence_by_goal.items():
            evidence_text += f"\n### {goal}\n"
            for ev in ev_list:
                evidence_text += f"- Found: {ev.found}\n"
                evidence_text += f"  Rationale: {ev.rationale}\n"
                evidence_text += f"  Confidence: {ev.confidence}\n"
                evidence_text += f"  Type: {ev.goal}\n"
                if ev.content and isinstance(ev.content, dict) and "analysis" in ev.content:
                    evidence_text += f"  Details: {json.dumps(ev.content.get('analysis', {}), indent=2)[:200]}\n"
        
        opinions = []
        
        # Process each criterion from rubric
        for dimension in rubric_loader.rubric.get("dimensions", []):
            criterion_id = dimension.get("id", "")
            
            # Skip if no evidence for this criterion
            relevant_evidence = []
            for ev in all_evidence:
                if dimension.get("name", "").lower() in ev.goal.lower() or criterion_id.lower() in ev.goal.lower():
                    relevant_evidence.append(ev)
            
            # Use mock in debug mode
            if DEBUG_MODE:
                mock = mock_judicial_opinion(criterion_id, judge_type)
                if mock:
                    opinions.append(mock)
                    continue
            
            # Prepare prompt for this criterion
            prompt = f"""{system_prompt}

CRITERION: {dimension.get('name', 'Unknown')} (ID: {criterion_id})
Target Artifact: {dimension.get('target_artifact', 'Unknown')}

SUCCESS PATTERN:
{dimension.get('success_pattern', 'No pattern specified')}

FAILURE PATTERN:
{dimension.get('failure_pattern', 'No pattern specified')}

EVIDENCE FOR THIS CRITERION:
{format_evidence_for_prompt(relevant_evidence)}

ALL AVAILABLE EVIDENCE (for context):
{evidence_text[:2000]}  # Truncated for token limits

Based STRICTLY on the evidence above, evaluate this criterion as {judge_type}.

Return a JSON object with:
{{
    "judge": "{judge_type}",
    "criterion_id": "{criterion_id}",
    "score": <integer 1-5>,
    "argument": <string explaining your reasoning, citing specific evidence>,
    "cited_evidence": <list of evidence goals you referenced>
}}
"""
            
            try:
                # Get LLM for judge tasks
                llm = get_llm_for_task("judge")
                
                # Invoke with JSON format
                response = llm.invoke(prompt)
                
                # Parse response
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                
                # Check for empty response
                if not response_text or response_text.strip() == "":
                    print(f"⚠️ LLM returned empty response for {criterion_id}")
                    # Use fallback opinion
                    opinions.append(JudicialOpinion(
                        judge=judge_type,
                        criterion_id=criterion_id,
                        score=3,
                        argument=f"LLM returned empty response for {criterion_id}",
                        cited_evidence=[]
                    ))
                    continue
                
                # Try to parse JSON
                try:
                    # Handle markdown code blocks
                    if response_text.strip().startswith('```json'):
                        # Extract JSON from markdown code block
                        start = response_text.find('{')
                        end = response_text.rfind('}')
                        if start != -1 and end != -1 and end > start:
                            json_str = response_text[start:end+1]
                            result = json.loads(json_str)
                        else:
                            raise json.JSONDecodeError("No valid JSON found in code block")
                    else:
                        result = json.loads(response_text)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parsing failed for {criterion_id}: {e}")
                    print(f"Response was: {response_text[:300]}...")
                    # Use fallback opinion
                    opinions.append(JudicialOpinion(
                        judge=judge_type,
                        criterion_id=criterion_id,
                        score=3,
                        argument=f"JSON parsing failed: {str(e)}",
                        cited_evidence=[]
                    ))
                    continue
                
                # Create JudicialOpinion
                opinion = JudicialOpinion(
                    judge=judge_type,
                    criterion_id=criterion_id,
                    score=result.get("score", 3),
                    argument=result.get("argument", "No argument provided"),
                    cited_evidence=result.get("cited_evidence", [])
                )
                opinions.append(opinion)
                
            except Exception as e:
                print(f"⚠️ {judge_type} failed for {criterion_id}: {e}")
                # Fallback opinion
                opinions.append(JudicialOpinion(
                    judge=judge_type,
                    criterion_id=criterion_id,
                    score=3,
                    argument=f"Evaluation failed: {str(e)}",
                    cited_evidence=[]
                ))
        
        return {"opinions": opinions}
    
    return judge_node


def format_evidence_for_prompt(evidence_list: List[Evidence]) -> str:
    """Format evidence list for inclusion in prompts"""
    if not evidence_list:
        return "No direct evidence found for this criterion."
    
    text = ""
    for ev in evidence_list:
        text += f"\n- Goal: {ev.goal}\n"
        text += f"  Found: {ev.found}\n"
        text += f"  Location: {ev.location}\n"
        text += f"  Rationale: {ev.rationale}\n"
        text += f"  Confidence: {ev.confidence}\n"
        
        # Add content summary if present
        if ev.content:
            if isinstance(ev.content, dict):
                # Truncate dict content
                content_str = json.dumps(ev.content, indent=2)[:300]
                text += f"  Content: {content_str}...\n"
            else:
                content_str = str(ev.content)[:300]
                text += f"  Content: {content_str}...\n"
    
    return text


# Convenience functions for graph construction
def prosecutor(state: AgentState) -> Dict[str, Any]:
    return create_judge_node("Prosecutor")(state)


def defense(state: AgentState) -> Dict[str, Any]:
    return create_judge_node("Defense")(state)


def tech_lead(state: AgentState) -> Dict[str, Any]:
    return create_judge_node("TechLead")(state)