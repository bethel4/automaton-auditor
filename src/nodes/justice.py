# src/nodes/justice.py

import json
from typing import Dict, List
from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport, Evidence

# Load rubric and synthesis rules
with open('rubric.json', 'r') as f:
    rubric = json.load(f)

synthesis_rules = rubric['synthesis_rules']

def chief_justice(state: AgentState) -> Dict:
    """Chief Justice synthesis engine with deterministic conflict resolution."""
    
    # Group opinions by criterion
    opinions_by_criterion = {}
    for opinion in state["opinions"]:
        criterion_id = opinion.criterion_id
        if criterion_id not in opinions_by_criterion:
            opinions_by_criterion[criterion_id] = []
        opinions_by_criterion[criterion_id].append(opinion)
    
    # Process each criterion
    criteria_results = []
    total_score = 0
    
    for dimension in rubric['dimensions']:
        criterion_id = dimension['id']
        criterion_name = dimension['name']
        
        # Get opinions for this criterion
        criterion_opinions = opinions_by_criterion.get(criterion_id, [])
        
        if not criterion_opinions:
            # No opinions available
            result = CriterionResult(
                dimension_id=criterion_id,
                dimension_name=criterion_name,
                final_score=1,
                judge_opinions=[],
                dissent_summary="No judicial opinions available",
                remediation="Unable to assess - no evidence provided"
            )
            criteria_results.append(result)
            total_score += 1
            continue
        
        # Apply synthesis rules
        final_score, dissent_summary = apply_synthesis_rules(
            criterion_opinions, dimension, state
        )
        
        # Generate remediation
        remediation = generate_remediation(criterion_opinions, dimension, final_score)
        
        result = CriterionResult(
            dimension_id=criterion_id,
            dimension_name=criterion_name,
            final_score=final_score,
            judge_opinions=criterion_opinions,
            dissent_summary=dissent_summary,
            remediation=remediation
        )
        
        criteria_results.append(result)
        total_score += final_score
    
    # Calculate overall score
    overall_score = total_score / len(rubric['dimensions']) if rubric['dimensions'] else 0
    
    # Generate executive summary
    executive_summary = generate_executive_summary(criteria_results, overall_score)
    
    # Generate overall remediation plan
    overall_remediation = generate_overall_remediation(criteria_results)
    
    # Create final audit report
    audit_report = AuditReport(
        repo_url=state["repo_url"],
        executive_summary=executive_summary,
        overall_score=overall_score,
        criteria=criteria_results,
        remediation_plan=overall_remediation
    )
    
    # Generate markdown report
    markdown_report = generate_markdown_report(audit_report)
    
    return {
        "final_report": audit_report,
        "markdown_report": markdown_report
    }

def apply_synthesis_rules(opinions: List[JudicialOpinion], dimension: Dict, state: AgentState) -> tuple[int, str]:
    """Apply deterministic synthesis rules to resolve conflicts."""
    
    scores = [op.score for op in opinions]
    max_score = max(scores)
    min_score = min(scores)
    variance = max_score - min_score
    
    # Rule 1: Security Override
    if dimension['id'] in ['safe_tool_engineering', 'structured_output_enforcement']:
        prosecutor_opinion = next((op for op in opinions if op.judge == "Prosecutor"), None)
        if prosecutor_opinion and prosecutor_opinion.score <= 2:
            # Security flaw detected - cap at 3
            final_score = min(3, max_score)
            dissent = f"Prosecutor identified security flaw, score capped at 3 (was {max_score})"
            return final_score, dissent
    
    # Rule 2: Fact Supremacy
    if dimension['id'] in ['state_management_rigor', 'graph_orchestration']:
        defense_opinion = next((op for op in opinions if op.judge == "Defense"), None)
        if defense_opinion and defense_opinion.score >= 4:
            # Check if evidence supports Defense claims
            evidence_key = f"{dimension['id']}_evidence"
            if not evidence_supports_claim(dimension['id'], state):
                final_score = min(3, min_score)
                dissent = f"Defense claims overruled - forensic evidence does not support assertions"
                return final_score, dissent
    
    # Rule 3: Functionality Weight (for architecture)
    if dimension['id'] == 'graph_orchestration':
        tech_lead_opinion = next((op for op in opinions if op.judge == "TechLead"), None)
        if tech_lead_opinion and tech_lead_opinion.score >= 4:
            final_score = tech_lead_opinion.score
            dissent = f"Tech Lead confirmation of modular architecture carries highest weight"
            return final_score, dissent
    
    # Rule 4: Variance Re-evaluation
    if variance > 2:
        # High disagreement - re-evaluate evidence
        final_score = calculate_weighted_score(opinions, state, dimension)
        dissent = f"High variance ({variance}) detected - applied weighted re-evaluation"
        return final_score, dissent
    
    # Default: Average with moderation
    final_score = int(round(sum(scores) / len(scores)))
    dissent = None
    
    if variance > 1:
        dissent = f"Moderate disagreement ({variance}) - averaged to {final_score}"
    
    return final_score, dissent

def evidence_supports_claim(dimension_id: str, state: AgentState) -> bool:
    """Check if forensic evidence supports claims."""
    evidences = []
    for evidence_list in state["evidences"].values():
        evidences.extend(evidence_list)
    
    # Look for evidence related to this dimension
    relevant_evidence = [ev for ev in evidences if dimension_id.lower() in ev.goal.lower()]
    
    # If evidence exists and has high confidence, support the claim
    return any(ev.confidence > 0.7 and ev.found for ev in relevant_evidence)

def calculate_weighted_score(opinions: List[JudicialOpinion], state: AgentState, dimension: Dict) -> int:
    """Calculate weighted score based on evidence support."""
    
    # Tech Lead gets highest weight for technical criteria
    if dimension['target_artifact'] == 'github_repo':
        tech_lead_opinion = next((op for op in opinions if op.judge == "TechLead"), None)
        if tech_lead_opinion:
            return tech_lead_opinion.score
    
    # For documentation criteria, Defense gets more weight
    elif dimension['target_artifact'] == 'pdf_report':
        defense_opinion = next((op for op in opinions if op.judge == "Defense"), None)
        if defense_opinion:
            return defense_opinion.score
    
    # Default to median
    scores = sorted([op.score for op in opinions])
    return scores[len(scores) // 2]

def generate_remediation(opinions: List[JudicialOpinion], dimension: Dict, final_score: int) -> str:
    """Generate specific remediation based on score and opinions."""
    
    if final_score >= 4:
        return "Excellent implementation. Maintain current standards."
    
    elif final_score == 3:
        return "Adequate but needs improvement. Focus on the specific issues identified by the judges."
    
    elif final_score == 2:
        remediation = f"Significant issues detected in {dimension['name']}. "
        
        # Add specific advice based on dimension
        if dimension['id'] == 'git_forensic_analysis':
            remediation += "Ensure atomic commits with clear progression. Avoid bulk uploads."
        elif dimension['id'] == 'state_management_rigor':
            remediation += "Implement proper Pydantic models with reducers for parallel execution."
        elif dimension['id'] == 'graph_orchestration':
            remediation += "Implement true parallel fan-out/fan-in patterns for both detectives and judges."
        elif dimension['id'] == 'safe_tool_engineering':
            remediation += "Use tempfile.TemporaryDirectory() and subprocess.run() with proper error handling."
        elif dimension['id'] == 'structured_output_enforcement':
            remediation += "Use .with_structured_output() with Pydantic schemas for all judge LLM calls."
        else:
            remediation += "Address the specific technical gaps identified in the evidence."
        
        return remediation
    
    else:  # final_score == 1
        return f"Critical failures in {dimension['name']}. Complete reimplementation required following the success pattern: {dimension['success_pattern']}"

def generate_executive_summary(criteria_results: List[CriterionResult], overall_score: float) -> str:
    """Generate executive summary of the audit."""
    
    high_scoring = [cr for cr in criteria_results if cr.final_score >= 4]
    low_scoring = [cr for cr in criteria_results if cr.final_score <= 2]
    
    summary = f"# Automaton Auditor Audit Report\n\n"
    summary += f"**Overall Score: {overall_score:.1f}/5.0**\n\n"
    
    if overall_score >= 4.0:
        summary += "## Executive Summary\n\n"
        summary += "This repository demonstrates excellent implementation of the Automaton Auditor architecture. "
        summary += "The system shows strong understanding of parallel orchestration, proper state management, and security practices.\n\n"
    elif overall_score >= 3.0:
        summary += "## Executive Summary\n\n"
        summary += "This repository shows competent implementation with several areas requiring improvement. "
        summary += "The basic architecture is sound but needs refinement in specific technical areas.\n\n"
    else:
        summary += "## Executive Summary\n\n"
        summary += "This repository requires significant improvements to meet the Automaton Auditor standards. "
        summary += "Critical architectural and security issues need to be addressed.\n\n"
    
    if high_scoring:
        summary += f"**Strengths ({len(high_scoring)} areas):** "
        summary += ", ".join([cr.dimension_name for cr in high_scoring]) + "\n\n"
    
    if low_scoring:
        summary += f"**Critical Issues ({len(low_scoring)} areas):** "
        summary += ", ".join([cr.dimension_name for cr in low_scoring]) + "\n\n"
    
    return summary

def generate_overall_remediation(criteria_results: List[CriterionResult]) -> str:
    """Generate overall remediation plan."""
    
    priority_issues = [cr for cr in criteria_results if cr.final_score <= 2]
    
    if not priority_issues:
        return "No critical issues identified. Continue maintaining current standards."
    
    remediation = "## Priority Remediation Plan\n\n"
    
    # Order by severity
    priority_issues.sort(key=lambda x: x.final_score)
    
    for i, issue in enumerate(priority_issues, 1):
        remediation += f"### {i}. {issue.dimension_name}\n\n"
        remediation += f"**Current Score: {issue.final_score}/5**\n\n"
        remediation += f"{issue.remediation}\n\n"
    
    return remediation

def generate_markdown_report(audit_report: AuditReport) -> str:
    """Generate complete markdown audit report."""
    
    report = audit_report.executive_summary + "\n\n"
    
    report += "## Detailed Criterion Breakdown\n\n"
    
    for criterion in audit_report.criteria:
        report += f"### {criterion.dimension_name}\n\n"
        report += f"**Final Score: {criterion.final_score}/5**\n\n"
        
        # Judge opinions
        if criterion.judge_opinions:
            report += "**Judicial Analysis:**\n\n"
            for opinion in criterion.judge_opinions:
                report += f"**{opinion.judge} (Score: {opinion.score}/5):** {opinion.argument}\n\n"
                if opinion.cited_evidence:
                    report += f"*Cited Evidence: {', '.join(opinion.cited_evidence)}*\n\n"
        
        # Dissent
        if criterion.dissent_summary:
            report += f"**Dissent Summary:** {criterion.dissent_summary}\n\n"
        
        # Remediation
        report += f"**Remediation:** {criterion.remediation}\n\n"
        report += "---\n\n"
    
    report += audit_report.remediation_plan + "\n\n"
    
    report += f"## Repository Information\n\n"
    report += f"- **Repository:** {audit_report.repo_url}\n"
    report += f"- **Overall Score:** {audit_report.overall_score:.1f}/5.0\n"
    report += f"- **Audit Date:** {json.dumps(rubric['rubric_metadata'])}\n"
    
    return report
