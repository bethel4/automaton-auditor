# src/nodes/judges.py

import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from langsmith import traceable

from src.state import AgentState, JudicialOpinion, Evidence
from src.llm_router import get_llm_for_task, get_fallback_llm, mock_judicial_opinion, DEBUG_MODE

# Persona-specific system prompts - with explicit JSON instructions
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

IMPORTANT: You MUST respond with ONLY a valid JSON object. No other text, no markdown, no explanations.

Return a JSON object with EXACTLY this structure:
{
    "score": 3,
    "argument": "Your detailed reasoning here, citing specific evidence",
    "cited_evidence": ["evidence goal 1", "evidence goal 2"]
}
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

IMPORTANT: You MUST respond with ONLY a valid JSON object. No other text, no markdown, no explanations.

Return a JSON object with EXACTLY this structure:
{
    "score": 3,
    "argument": "Your detailed reasoning here, citing specific evidence",
    "cited_evidence": ["evidence goal 1", "evidence goal 2"]
}
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

IMPORTANT: You MUST respond with ONLY a valid JSON object. No other text, no markdown, no explanations.

Return a JSON object with EXACTLY this structure:
{
    "score": 3,
    "argument": "Your detailed reasoning here, citing specific evidence",
    "cited_evidence": ["evidence goal 1", "evidence goal 2"]
}
"""


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract JSON from LLM response, handling various formats
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Extracted JSON as dictionary
    """
    if not response_text:
        print("⚠️ Empty response from LLM")
        return {"score": 3, "argument": "Empty response from LLM", "cited_evidence": []}
    
    # Print first 200 chars for debugging
    print(f"\n📝 Raw response (first 200 chars): {response_text[:200]}")
    
    # Try to find JSON in markdown code blocks
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, response_text)
    
    if matches:
        for match in matches:
            try:
                cleaned = match.strip()
                result = json.loads(cleaned)
                print(f"✅ Found JSON in code block")
                return result
            except json.JSONDecodeError as e:
                print(f"⚠️ Code block contains invalid JSON: {e}")
                continue
    
    # Try to find JSON object directly (between first { and last })
    try:
        start = response_text.find('{')
        end = response_text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = response_text[start:end+1]
            # Clean up common issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            result = json.loads(json_str)
            print(f"✅ Found JSON object directly")
            return result
    except json.JSONDecodeError as e:
        print(f"⚠️ Direct JSON parsing failed: {e}")
    
    # Try parsing the entire response
    try:
        cleaned = response_text.strip()
        result = json.loads(cleaned)
        print(f"✅ Parsed entire response as JSON")
        return result
    except json.JSONDecodeError:
        pass
    
    # If all else fails, try to extract score using regex
    print(f"⚠️ Could not parse JSON, attempting fallback extraction")
    
    # Try to extract score
    score_match = re.search(r'score["\s]*:["\s]*(\d+)', response_text, re.IGNORECASE)
    score = int(score_match.group(1)) if score_match else 3
    
    # Try to extract argument
    argument_match = re.search(r'argument["\s]*:["\s]*"([^"]+)"', response_text, re.IGNORECASE)
    argument = argument_match.group(1) if argument_match else "Failed to parse LLM response"
    
    # Try to extract cited_evidence
    evidence = []
    evidence_match = re.search(r'cited_evidence["\s]*:["\s]*\[(.*?)\]', response_text, re.IGNORECASE | re.DOTALL)
    if evidence_match:
        evidence_str = evidence_match.group(1)
        evidence = [e.strip().strip('"\'') for e in evidence_str.split(',') if e.strip()]
    
    return {
        "score": score,
        "argument": argument,
        "cited_evidence": evidence
    }


def create_judge_node(judge_type: str):
    """
    Factory function to create judge nodes with proper persona
    """
    
    def judge_node(state: AgentState) -> Dict[str, Any]:
        """Judge node that evaluates evidence through persona lens"""
        
        print(f"\n{'='*60}")
        print(f"⚖️ {judge_type} NODE STARTED")
        print(f"{'='*60}")
        
        # DEBUG: Print all evidence received
        evidences = state.get("evidences", {})
        print(f"\n📋 Evidence received by {judge_type}:")
        print(f"  Keys in evidences dict: {list(evidences.keys())}")
        
        if not evidences:
            print("  ❌ No evidence found in state!")
        else:
            # Count total evidence items
            total_items = 0
            for detective, ev_list in evidences.items():
                print(f"\n  📁 From {detective}: {len(ev_list)} evidence items")
                for i, ev in enumerate(ev_list):
                    print(f"    {i+1}. Goal: {ev.goal}")
                    print(f"       Found: {ev.found}")
                    print(f"       Confidence: {ev.confidence}")
                    total_items += 1
            
            print(f"\n  📊 TOTAL EVIDENCE ITEMS: {total_items}")
        
        # Select prompt based on judge type
        if judge_type == "Prosecutor":
            system_prompt = PROSECUTOR_PROMPT
        elif judge_type == "Defense":
            system_prompt = DEFENSE_PROMPT
        else:  # TechLead
            system_prompt = TECH_LEAD_PROMPT
        
        # Get rubric from config
        rubric_loader = state["config"]["rubric"]
        
        # Get all evidence
        all_evidence = []
        evidence_by_goal = {}
        
        for detective_name, evidence_list in state.get("evidences", {}).items():
            for evidence in evidence_list:
                all_evidence.append(evidence)
                if evidence.goal not in evidence_by_goal:
                    evidence_by_goal[evidence.goal] = []
                evidence_by_goal[evidence.goal].append(evidence)
        
        opinions = []
        
        # Process each criterion from rubric
        for dimension in rubric_loader.rubric.get("dimensions", []):
            criterion_id = dimension.get("id", dimension.get("dimension_id", "unknown"))
            
            # Skip if no evidence for this criterion
            relevant_evidence = []
            dimension_name = dimension.get("name", "unknown")
            for ev in all_evidence:
                if (dimension_name.lower() in ev.goal.lower() or 
                    criterion_id.lower() in ev.goal.lower() or
                    any(word in ev.goal.lower() for word in dimension_name.lower().split())):
                    relevant_evidence.append(ev)
            
            # Use mock in debug mode
            if DEBUG_MODE:
                mock = mock_judicial_opinion(criterion_id, judge_type)
                if mock:
                    opinions.append(mock)
                    continue
            
            # Prepare evidence text
            evidence_text = format_evidence_for_prompt(relevant_evidence) if relevant_evidence else "No specific evidence found for this criterion."
            
            # Prepare prompt for this criterion
            prompt = f"""{system_prompt}

CRITERION: {dimension_name}
ID: {criterion_id}

SUCCESS PATTERN:
{dimension.get('success_pattern', 'Not specified')}

FAILURE PATTERN:
{dimension.get('failure_pattern', 'Not specified')}

EVIDENCE:
{evidence_text}

Based STRICTLY on the evidence above, evaluate this criterion as {judge_type}.

Remember: Return ONLY a JSON object with no other text.
"""
            
            try:
                # Get LLM for judge tasks
                llm = get_llm_for_task("judge")
                
                print(f"\n⚖️ {judge_type} evaluating {criterion_id}...")
                
                # Invoke with metadata for better tracing
                response = llm.invoke(
                    prompt,
                    config={
                        "tags": ["judge", judge_type.lower(), "adversarial"],
                        "metadata": {
                            "persona": judge_type,
                            "criterion_id": criterion_id,
                            "philosophy": PROSECUTOR_PROMPT if judge_type == "Prosecutor" else DEFENSE_PROMPT if judge_type == "Defense" else TECH_LEAD_PROMPT
                        }
                    }
                )
                
                # Get response text
                if hasattr(response, 'content'):
                    response_text = response.content
                else:
                    response_text = str(response)
                
                # Extract JSON from response
                result = extract_json_from_response(response_text)
                
                # Create JudicialOpinion
                opinion = JudicialOpinion(
                    judge=judge_type,
                    criterion_id=criterion_id,
                    score=result.get("score", 3),
                    argument=result.get("argument", f"No argument provided for {criterion_id}"),
                    cited_evidence=result.get("cited_evidence", [])
                )
                opinions.append(opinion)
                print(f"✅ {judge_type} scored {criterion_id}: {opinion.score}/5")
                
            except Exception as e:
                print(f"⚠️ {judge_type} failed for {criterion_id}: {e}")
                import traceback
                traceback.print_exc()
                
                # Fallback opinion
                opinions.append(JudicialOpinion(
                    judge=judge_type,
                    criterion_id=criterion_id,
                    score=3,
                    argument=f"Evaluation failed: {str(e)}. Using default score.",
                    cited_evidence=[]
                ))
        
        return {"opinions": opinions}
    
    return judge_node


def format_evidence_for_prompt(evidence_list: List[Evidence]) -> str:
    """Format evidence list for inclusion in prompts"""
    if not evidence_list:
        return "No evidence found for this criterion."
    
    text = ""
    for i, ev in enumerate(evidence_list, 1):
        text += f"\nEVIDENCE {i}:\n"
        text += f"  Goal: {ev.goal}\n"
        text += f"  Found: {ev.found}\n"
        text += f"  Location: {ev.location}\n"
        text += f"  Rationale: {ev.rationale}\n"
        text += f"  Confidence: {ev.confidence}\n"
        
        # Add content summary if present and useful
        if ev.content and ev.found:
            if isinstance(ev.content, dict):
                if "progression_score" in ev.content:
                    text += f"  Progression Score: {ev.content.get('progression_score', 'N/A')}\n"
                if "safety_score" in ev.content:
                    text += f"  Safety Score: {ev.content.get('safety_score', 'N/A')}\n"
                if "has_pydantic" in ev.content:
                    text += f"  Has Pydantic: {ev.content.get('has_pydantic', False)}\n"
                if "has_reducers" in ev.content:
                    text += f"  Has Reducers: {ev.content.get('has_reducers', False)}\n"
    
    return text


# Convenience functions for graph construction
@traceable(name="prosecutor", run_type="llm")
def prosecutor(state: AgentState) -> Dict[str, Any]:
    return create_judge_node("Prosecutor")(state)


@traceable(name="defense", run_type="llm")
def defense(state: AgentState) -> Dict[str, Any]:
    return create_judge_node("Defense")(state)


@traceable(name="tech_lead", run_type="llm")
def tech_lead(state: AgentState) -> Dict[str, Any]:
    return create_judge_node("TechLead")(state)