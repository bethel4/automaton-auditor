# src/nodes/detectives.py

import os
import ast
import json
from typing import Dict, List, Any
from pathlib import Path

from src.state import AgentState, Evidence
from tools.repo_tools import clone_repository, extract_git_history, analyze_graph_structure
from tools.doc_tools import ingest_pdf, query_pdf

# Initialize LLM for pattern recognition (lazy loading)
llm = None

def get_llm():
    """Lazy LLM initialization to avoid import errors."""
    global llm
    if llm is None:
        from src.llm import get_llm as init_llm
        llm = init_llm()
    return llm

def repo_investigator(state: AgentState) -> Dict[str, Any]:
    """Detective: Git forensic analysis with LLM pattern recognition."""
    repo_url = state["repo_url"]
    evidences = []
    
    try:
        repo_path = clone_repository(repo_url)
        
        # Extract git history for LLM analysis
        commits = extract_git_history(repo_path)
        
        # LLM Pattern Recognition for Git Analysis
        llm_instance = get_llm()
        pattern_analysis = llm_instance.invoke(f"""
        You are a forensic software engineer analyzing git commit history.
        
        Commits found:
        {chr(10).join(commits[:20])}
        
        Analyze DEVELOPMENT STORY and answer:
        1. Is this a HEALTHY progression or CHAOTIC?
        2. Does developer UNDERSTAND architecture or just hacking?
        3. What's PATTERN of development?
        4. Rate DISCIPLINE of development (1-5)
        
        Return JSON:
        {{
            "pattern_type": "disciplined|messy|bulk_upload|iterative",
            "story": "brief narrative of development approach",
            "discipline_score": 1-5,
            "evidence": "quotes from commits that support your analysis"
        }}
        """)
        
        try:
            analysis = json.loads(pattern_analysis.content)
            evidence = Evidence(
                goal="Git Forensic Analysis",
                found=True,
                content=analysis,
                location=repo_url,
                rationale=f"Pattern type: {analysis.get('pattern_type', 'unknown')}, Score: {analysis.get('discipline_score', 0)}",
                confidence=0.8
            )
            evidences.append(evidence)
        except:
            # Fallback to basic analysis
            evidence = Evidence(
                goal="Git Forensic Analysis",
                found=True,
                content={"commits_analyzed": len(commits)},
                location=repo_url,
                rationale="Basic git history extraction completed",
                confidence=0.6
            )
            evidences.append(evidence)
        
        # Analyze graph structure
        graph_analysis = analyze_graph_structure(repo_path)
        if graph_analysis:
            evidence = Evidence(
                goal="Graph Architecture Analysis",
                found=True,
                content=graph_analysis,
                location=repo_path,
                rationale="AST analysis of LangGraph structure",
                confidence=0.7
            )
            evidences.append(evidence)
        
        return {"evidences": {"repo_analysis": evidences}}
        
    except Exception as e:
        error_evidence = Evidence(
            goal="Repository Analysis",
            found=False,
            content=None,
            location=repo_url,
            rationale=f"Failed to analyze repository: {str(e)}",
            confidence=0.1,
        )
        return {"evidences": {"repo_analysis": [error_evidence]}}

def doc_analyst(state: AgentState) -> Dict[str, Any]:
    """Detective: PDF analysis with LLM quality assessment."""
    pdf_path = state["pdf_path"]
    evidences = []
    
    try:
        if not os.path.exists(pdf_path):
            # Try to create a basic PDF if it doesn't exist
            evidences.append(Evidence(
                goal="PDF Analysis",
                found=False,
                content=None,
                location=pdf_path,
                rationale="PDF file not found",
                confidence=0.0
            ))
            return {"evidences": {"doc_analysis": evidences}}
        
        # Ingest PDF content
        pdf_content = ingest_pdf(pdf_path)
        
        # LLM Quality Assessment
        llm_instance = get_llm()
        quality_analysis = llm_instance.invoke(f"""
        You are a technical documentation analyst evaluating a project report.
        
        PDF content extracted:
        {pdf_content[:1000]}...
        
        Assess DOCUMENTATION QUALITY:
        1. Technical depth and accuracy
        2. Clarity and organization
        3. Completeness of coverage
        4. Professional presentation
        
        Return JSON:
        {{
            "quality_score": 1-5,
            "strengths": ["list of strengths"],
            "weaknesses": ["list of weaknesses"],
            "technical_depth": "shallow|moderate|deep",
            "overall_assessment": "brief evaluation"
        }}
        """)
        
        try:
            analysis = json.loads(quality_analysis.content)
            evidence = Evidence(
                goal="Documentation Quality Analysis",
                found=True,
                content=analysis,
                location=pdf_path,
                rationale=f"Quality score: {analysis.get('quality_score', 0)}/5",
                confidence=0.8
            )
            evidences.append(evidence)
        except:
            # Fallback to basic analysis
            evidence = Evidence(
                goal="Documentation Analysis",
                found=True,
                content={"content_length": len(pdf_content)},
                location=pdf_path,
                rationale="Basic PDF content extraction completed",
                confidence=0.6
            )
            evidences.append(evidence)
        
        return {"evidences": {"doc_analysis": evidences}}
        
    except Exception as e:
        error_evidence = Evidence(
            goal="Documentation Analysis",
            found=False,
            content=None,
            location=pdf_path,
            rationale=f"Failed to analyze documentation: {str(e)}",
            confidence=0.1,
        )
        return {"evidences": {"doc_analysis": [error_evidence]}}

def vision_inspector(state: AgentState) -> Dict[str, Any]:
    """Detective: Placeholder for multimodal diagram analysis."""
    evidences = []
    
    # Placeholder for future VisionInspector implementation
    evidence = Evidence(
        goal="Visual Diagram Analysis",
        found=False,
        content=None,
        location="N/A",
        rationale="VisionInspector not yet implemented - requires multimodal LLM",
        confidence=0.0
    )
    evidences.append(evidence)
    
    return {"evidences": {"vision_analysis": evidences}}
