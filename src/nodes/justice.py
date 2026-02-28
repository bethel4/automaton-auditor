# src/nodes/justice.py

import json
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

from langsmith import traceable

from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport, Evidence


@traceable(name="chief_justice", run_type="chain")
def chief_justice(state: AgentState) -> Dict[str, Any]:
    """
    Chief Justice synthesizes judge opinions with deterministic rules
    
    Synthesis Rules (from rubric):
    1. Security Override: Security flaws cap score at 3
    2. Fact Supremacy: Forensic evidence overrules judicial opinion
    3. Functionality Weight: Tech Lead carries highest weight for architecture
    4. Dissent Requirement: Summarize disagreements when variance > 2
    5. Variance Re-evaluation: Trigger re-evaluation if variance > 2
    """
    
    # Get rubric from config
    rubric_loader = state["config"]["rubric"]
    
    # Group opinions by criterion
    opinions_by_criterion = defaultdict(list)
    for opinion in state.get("opinions", []):
        opinions_by_criterion[opinion.criterion_id].append(opinion)
    
    # Get all evidence for fact checking
    all_evidence = []
    for evidence_list in state.get("evidences", {}).values():
        all_evidence.extend(evidence_list)
    
    # Process each criterion
    criteria_results = []
    total_score = 0
    
    for dimension in rubric_loader.rubric.get("dimensions", []):
        criterion_id = dimension.get("id", dimension.get("dimension_id", "unknown"))
        dimension_name = dimension.get("name", "unknown")
        opinions = opinions_by_criterion.get(criterion_id, [])
        
        if not opinions:
            # No opinions for this criterion
            result = CriterionResult(
                dimension_id=criterion_id,
                name=dimension_name,
                final_score=1,
                judge_opinions=[],
                dissent_summary="No judicial opinions available",
                remediation=f"Missing evaluation for {dimension_name}. Ensure all judges process this criterion."
            )
            criteria_results.append(result)
            total_score += 1
            continue
        
        # Apply synthesis rules to determine final score
        final_score, dissent = synthesize_criterion(
            criterion_id=criterion_id,
            dimension=dimension,
            opinions=opinions,
            evidence=all_evidence,
            rubric_loader=rubric_loader
        )
        
        # Generate remediation based on score and opinions
        remediation = generate_remediation(
            criterion_id=criterion_id,
            dimension=dimension,
            dimension_name=dimension_name,
            final_score=final_score,
            opinions=opinions,
            evidence=all_evidence
        )
        
        result = CriterionResult(
            dimension_id=criterion_id,
            name=dimension_name,
            final_score=final_score,
            judge_opinions=opinions,
            dissent_summary=dissent,
            remediation=remediation
        )
        
        criteria_results.append(result)
        total_score += final_score
    
    # Calculate overall score
    overall_score = total_score / len(criteria_results) if criteria_results else 0
    
    # Generate executive summary
    executive_summary = generate_executive_summary(criteria_results, overall_score)
    
    # Generate overall remediation plan
    remediation_plan = generate_remediation_plan(criteria_results)
    
    # Create final audit report
    audit_report = AuditReport(
        repo_url=state["repo_url"],
        executive_summary=executive_summary,
        overall_score=overall_score,
        criteria=criteria_results,
        remediation_plan=remediation_plan
    )
    
    # Generate markdown report
    markdown_report = generate_markdown_report(audit_report)
    
    return {
        "final_report": audit_report,
        "markdown_report": markdown_report
    }


def synthesize_criterion(
    criterion_id: str,
    dimension: Any,
    opinions: List[JudicialOpinion],
    evidence: List[Evidence],
    rubric_loader: Any
) -> tuple[int, Optional[str]]:
    """
    Apply deterministic synthesis rules to resolve conflicts
    
    Returns:
        Tuple of (final_score, dissent_summary)
    """
    
    # Extract scores
    scores = [op.score for op in opinions]
    avg_score = sum(scores) / len(scores)
    variance = max(scores) - min(scores)
    
    # Find opinions by judge type
    prosecutor = next((op for op in opinions if op.judge == "Prosecutor"), None)
    defense = next((op for op in opinions if op.judge == "Defense"), None)
    tech_lead = next((op for op in opinions if op.judge == "TechLead"), None)
    
    dissent = None
    
    # --- RULE 1: Security Override ---
    # If Prosecutor identifies security flaw, cap at 3
    if prosecutor and prosecutor.score <= 2 and "security" in prosecutor.argument.lower():
        # Check if security flaw is confirmed by evidence
        security_confirmed = False
        for ev in evidence:
            if ev.goal == "Safe Tool Engineering" and ev.found is False:
                security_confirmed = True
            if "security" in ev.goal.lower() and ev.found is False:
                security_confirmed = True
        
        if security_confirmed:
            final_score = min(3, int(round(avg_score)))
            dissent = f"SECURITY OVERRIDE: Prosecutor identified security flaw (score {prosecutor.score}). Score capped at 3."
            return final_score, dissent
    
    # --- RULE 2: Fact Supremacy ---
    # If Defense claims high score but evidence contradicts, overrule
    if defense and defense.score >= 4:
        # Check if evidence supports high score
        evidence_supports = check_evidence_supports_score(criterion_id, evidence, high_score=True)
        
        if not evidence_supports:
            # Overrule Defense
            non_defense_scores = [op.score for op in opinions if op.judge != "Defense"]
            if non_defense_scores:
                final_score = int(round(sum(non_defense_scores) / len(non_defense_scores)))
            else:
                final_score = 3
            
            dissent = f"FACT SUPREMACY: Defense claimed {defense.score} but evidence doesn't support. Using other judges' scores."
            return final_score, dissent
    
    # --- RULE 3: Functionality Weight ---
    # For architecture criteria, Tech Lead carries highest weight
    if criterion_id in ["graph_orchestration", "state_management_rigor"] and tech_lead:
        # Tech Lead gets 2x weight
        weighted_sum = tech_lead.score * 2
        weighted_count = 2
        
        for op in opinions:
            if op.judge != "TechLead":
                weighted_sum += op.score
                weighted_count += 1
        
        final_score = int(round(weighted_sum / weighted_count))
        dissent = f"FUNCTIONALITY WEIGHT: Tech Lead opinion weighted more heavily for architecture."
        return final_score, dissent
    
    # --- RULE 4: Variance Re-evaluation ---
    if variance > 2:
        # High disagreement - use weighted approach based on evidence confidence
        final_score = calculate_weighted_score(opinions, evidence, criterion_id)
        dissent = f"HIGH VARIANCE ({variance}): Applied evidence-weighted re-evaluation. Original scores: {scores}"
        return final_score, dissent
    
    # Default: average with rounding
    final_score = int(round(avg_score))
    
    # Add dissent if there's meaningful disagreement
    if variance > 1:
        dissent = f"Moderate disagreement (variance {variance}). Final score {final_score} from scores {scores}"
    
    return final_score, dissent


def check_evidence_supports_score(criterion_id: str, evidence: List[Evidence], high_score: bool) -> bool:
    """Check if evidence supports a high or low score"""
    
    # Find relevant evidence
    relevant = []
    for ev in evidence:
        if criterion_id.replace("_", " ") in ev.goal.lower():
            relevant.append(ev)
    
    if not relevant:
        return False
    
    # For high score, need high-confidence positive evidence
    if high_score:
        positive_high_conf = [ev for ev in relevant if ev.found and ev.confidence > 0.7]
        return len(positive_high_conf) >= 1
    
    # For low score, need negative evidence or low confidence
    else:
        negative = [ev for ev in relevant if not ev.found]
        return len(negative) >= 1


def calculate_weighted_score(
    opinions: List[JudicialOpinion], 
    evidence: List[Evidence], 
    criterion_id: str
) -> int:
    """Calculate weighted score based on evidence support for each opinion"""
    
    weighted_sum = 0
    total_weight = 0
    
    for opinion in opinions:
        # Base weight
        weight = 1.0
        
        # Increase weight if opinion cites evidence
        if opinion.cited_evidence:
            # Check if cited evidence exists and has high confidence
            for cited in opinion.cited_evidence:
                for ev in evidence:
                    if ev.goal == cited and ev.confidence > 0.8:
                        weight += 0.5
        
        # Adjust based on judge type
        if opinion.judge == "TechLead" and criterion_id in ["graph_orchestration", "state_management_rigor"]:
            weight += 0.5  # Tech Lead more important for architecture
        
        weighted_sum += opinion.score * weight
        total_weight += weight
    
    return int(round(weighted_sum / total_weight))


def generate_remediation(
    criterion_id: str,
    dimension: Any,
    dimension_name: str,
    final_score: int,
    opinions: List[JudicialOpinion],
    evidence: List[Evidence]
) -> str:
    """Generate specific remediation based on score and opinions"""
    
    if final_score >= 4:
        return f"✅ EXCELLENT: {dimension_name} meets or exceeds expectations. Maintain current practices."
    
    elif final_score == 3:
        # Find specific issues from low-scoring judges
        issues = []
        for op in opinions:
            if op.score <= 2:
                issues.append(f"{op.judge}: {op.argument[:100]}")
        
        if issues:
            return f"⚠️ ADEQUATE WITH ISSUES: {dimension_name} needs improvement.\n" + "\n".join(issues[:2])
        else:
            return f"⚠️ {dimension_name} is adequate but could be improved. Review the success pattern: {dimension.get('success_pattern', 'N/A')}"
    
    elif final_score == 2:
        # Significant issues - provide specific fixes
        if criterion_id == "git_forensic_analysis":
            return "🔧 FIX: Create atomic commits showing progression (setup → tools → graph). Avoid bulk uploads. Use meaningful commit messages."
        
        elif criterion_id == "state_management_rigor":
            return "🔧 FIX: Implement Pydantic BaseModel classes for Evidence, JudicialOpinion, AuditReport. Add Annotated reducers with operator.ior/operator.add for parallel execution."
        
        elif criterion_id == "graph_orchestration":
            return "🔧 FIX: Implement parallel fan-out for detectives and judges. Add EvidenceAggregator node. Use proper state reducers."
        
        elif criterion_id == "safe_tool_engineering":
            return "🔧 FIX: Use tempfile.TemporaryDirectory() for git clones. Replace os.system() with subprocess.run(). Add error handling."
        
        elif criterion_id == "structured_output_enforcement":
            return "🔧 FIX: Use .with_structured_output() with JudicialOpinion schema for all judge LLM calls. Add retry logic."
        
        elif criterion_id == "judicial_nuance":
            return "🔧 FIX: Create three distinct judge personas with conflicting prompts. Ensure they run in parallel on same evidence."
        
        elif criterion_id == "chief_justice_synthesis":
            return "🔧 FIX: Implement deterministic conflict resolution rules (security override, fact supremacy). Generate Markdown report."
        
        else:
            return f"🔧 FIX: Address issues in {dimension_name}. Success pattern: {dimension.get('success_pattern', 'N/A')}"
    
    else:  # score 1
        return f"❌ CRITICAL: {dimension_name} is missing or fundamentally broken. Complete reimplementation required following: {dimension.get('success_pattern', 'N/A')}"


def generate_executive_summary(criteria_results: List[CriterionResult], overall_score: float) -> str:
    """Generate executive summary of the audit"""
    
    # Categorize results
    excellent = [c for c in criteria_results if c.final_score >= 4]
    good = [c for c in criteria_results if c.final_score == 3]
    poor = [c for c in criteria_results if c.final_score <= 2]
    
    summary = f"# Automaton Auditor Report\n\n"
    summary += f"**Overall Score: {overall_score:.1f}/5.0**\n\n"
    
    # Score interpretation
    if overall_score >= 4.0:
        summary += "## 🏆 EXCELLENT\n\n"
        summary += "This repository demonstrates strong understanding of the Automaton Auditor architecture. "
        summary += "The implementation shows proper use of parallel execution, state management, and forensic analysis.\n\n"
    elif overall_score >= 3.0:
        summary += "## 👍 COMPETENT\n\n"
        summary += "This repository shows competent implementation with room for improvement. "
        summary += "Core concepts are present but need refinement in specific areas.\n\n"
    elif overall_score >= 2.0:
        summary += "## ⚠️ NEEDS IMPROVEMENT\n\n"
        summary += "This repository has significant gaps. Focus on addressing the critical issues identified below.\n\n"
    else:
        summary += "## ❌ CRITICAL ISSUES\n\n"
        summary += "This repository requires substantial rework to meet specifications. "
        summary += "Review the rubric carefully and rebuild core components.\n\n"
    
    # Summary stats
    summary += f"### Summary Statistics\n\n"
    summary += f"- **Excellent (4-5):** {len(excellent)} criteria\n"
    summary += f"- **Adequate (3):** {len(good)} criteria\n"
    summary += f"- **Poor (1-2):** {len(poor)} criteria\n\n"
    
    # Key findings
    if excellent:
        summary += f"### ✅ Strengths\n\n"
        for c in excellent[:3]:  # Top 3
            summary += f"- **{c.name}** (Score: {c.final_score}/5): {c.remediation[:100]}...\n"
        summary += "\n"
    
    if poor:
        summary += f"### 🔧 Critical Issues\n\n"
        for c in poor:
            summary += f"- **{c.name}** (Score: {c.final_score}/5): {c.remediation}\n"
        summary += "\n"
    
    return summary


def generate_remediation_plan(criteria_results: List[CriterionResult]) -> str:
    """Generate overall remediation plan"""
    
    # Sort by score (lowest first)
    sorted_results = sorted(criteria_results, key=lambda x: x.final_score)
    
    plan = "## 🔧 Remediation Plan\n\n"
    plan += "### Priority Issues (Fix First)\n\n"
    
    # Priority 1: Scores 1-2
    priority1 = [c for c in sorted_results if c.final_score <= 2]
    if priority1:
        for i, criterion in enumerate(priority1, 1):
            plan += f"**{i}. {criterion.name}** (Score: {criterion.final_score}/5)\n\n"
            plan += f"{criterion.remediation}\n\n"
    else:
        plan += "No critical issues found.\n\n"
    
    # Priority 2: Scores 3
    priority2 = [c for c in sorted_results if c.final_score == 3]
    if priority2:
        plan += "### Secondary Improvements\n\n"
        for criterion in priority2:
            plan += f"- **{criterion.name}**: {criterion.remediation}\n"
        plan += "\n"
    
    # File-level instructions
    plan += "### 📁 File-Level Instructions\n\n"
    
    file_instructions = {
        "src/state.py": "Ensure Pydantic models with proper reducers",
        "src/graph.py": "Implement parallel fan-out/fan-in with StateGraph",
        "src/nodes/detectives.py": "Add deterministic forensic tools",
        "src/nodes/judges.py": "Create three distinct judge personas with structured output",
        "src/nodes/justice.py": "Implement deterministic synthesis rules",
        "src/tools/repo_tools.py": "Add sandboxed git operations with tempfile",
        "reports/final_report.pdf": "Document architecture decisions and self-audit"
    }
    
    for file_path, instruction in file_instructions.items():
        plan += f"- **{file_path}**: {instruction}\n"
    
    return plan


def generate_markdown_report(report: AuditReport) -> str:
    """Generate complete markdown audit report"""
    
    md = report.executive_summary + "\n\n"
    
    md += "## 📊 Detailed Criterion Breakdown\n\n"
    
    for criterion in report.criteria:
        md += f"### {criterion.name}\n\n"
        md += f"**Final Score: {criterion.final_score}/5**\n\n"
        
        # Judge opinions
        if criterion.judge_opinions:
            md += "#### Judicial Opinions\n\n"
            
            for opinion in criterion.judge_opinions:
                # Icon based on judge
                icon = "👨‍⚖️" if opinion.judge == "Prosecutor" else "👩‍⚖️" if opinion.judge == "Defense" else "👨‍💻"
                
                md += f"**{icon} {opinion.judge}** (Score: {opinion.score}/5)\n\n"
                md += f"{opinion.argument}\n\n"
                
                if opinion.cited_evidence:
                    md += f"*Evidence cited: {', '.join(opinion.cited_evidence)}*\n\n"
        
        # Dissent summary
        if criterion.dissent_summary:
            md += f"#### ⚖️ Dissent Summary\n\n"
            md += f"{criterion.dissent_summary}\n\n"
        
        # Remediation
        md += f"#### 🔧 Remediation\n\n"
        md += f"{criterion.remediation}\n\n"
        
        md += "---\n\n"
    
    # Add remediation plan
    md += report.remediation_plan + "\n\n"
    
    # Add metadata
    md += "---\n\n"
    md += f"*Report generated by Automaton Auditor*\n"
    md += f"*Repository: {report.repo_url}*\n"
    md += f"*Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    return md