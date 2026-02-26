# src/nodes/detectives.py

import base64
import os
import ast
import json
from typing import Dict, List, Any
from pathlib import Path

from langchain_core.messages import HumanMessage

from src.state import AgentState, Evidence
from tools.repo_tools import (
    clone_repository,
    extract_git_history,
    analyze_graph_structure,
    ingest_repository_with_gitingest,
)
from tools.doc_tools import ingest_pdf, query_pdf, extract_images_from_pdf

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

        # Optional: high-level codebase digest via gitingest
        gitingest_token = os.getenv("GITHUB_TOKEN")
        digest = ingest_repository_with_gitingest(
            repo_url,
            token=gitingest_token,
        )
        
        # LLM Pattern Recognition for Git Analysis
        llm_instance = get_llm()
        pattern_analysis = llm_instance.invoke(f"""
        You are a forensic software engineer analyzing git commit history.
        
        Commits found (first 20):
        {chr(10).join(commits[:20])}

        Repository digest (from gitingest, truncated):
        SUMMARY:
        {digest.get("summary", "")[:2000]}
        
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
    # Optional: a specific question such as
    # "What does the report say about Dialectical Synthesis?"
    question = state.get("doc_question")
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
        
        # Ingest PDF content with Docling-backed chunking
        pdf_chunks = ingest_pdf(pdf_path)

        # If a specific question is provided, focus on matching chunks
        if question:
            relevant_chunks = query_pdf(pdf_chunks, question)
            context_snippet = "\n\n---\n\n".join(relevant_chunks[:5])
        else:
            # Fallback: just use the first few chunks as a quality sample
            context_snippet = "\n\n---\n\n".join(pdf_chunks[:5])
        
        # LLM Quality Assessment
        llm_instance = get_llm()
        if question:
            prompt = f"""
            You are a technical documentation analyst evaluating a project report.

            The user question is:
            \"{question}\"

            Here are the most relevant excerpts from the PDF:
            {context_snippet}

            Answer the user's question concisely, using ONLY the provided excerpts.
            """
        else:
            prompt = f"""
            You are a technical documentation analyst evaluating a project report.

            Sample content extracted from the PDF:
            {context_snippet}

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
            """

        quality_analysis = llm_instance.invoke(prompt)
        
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
    """Detective: Multimodal diagram analysis for StateGraph detection."""
    evidences: List[Evidence] = []

    pdf_path = state.get("pdf_path")
    if not pdf_path or not isinstance(pdf_path, str):
        evidences.append(
            Evidence(
                goal="Visual Diagram Analysis",
                found=False,
                content=None,
                location=str(pdf_path),
                rationale="No PDF path provided for visual analysis",
                confidence=0.0,
            )
        )
        return {"evidences": {"vision_analysis": evidences}}

    # Only attempt visual analysis on actual PDF files
    if not os.path.exists(pdf_path) or not pdf_path.lower().endswith(".pdf"):
        evidences.append(
            Evidence(
                goal="Visual Diagram Analysis",
                found=False,
                content=None,
                location=pdf_path,
                rationale="PDF file for visual analysis not found or not a .pdf",
                confidence=0.0,
            )
        )
        return {"evidences": {"vision_analysis": evidences}}

    try:
        images = extract_images_from_pdf(pdf_path)
    except Exception as e:
        evidences.append(
            Evidence(
                goal="Visual Diagram Analysis",
                found=False,
                content=None,
                location=pdf_path,
                rationale=f"Failed to extract images from PDF: {e}",
                confidence=0.1,
            )
        )
        return {"evidences": {"vision_analysis": evidences}}

    if not images:
        evidences.append(
            Evidence(
                goal="Visual Diagram Analysis",
                found=False,
                content={"images_found": 0},
                location=pdf_path,
                rationale="No images found in PDF for visual analysis",
                confidence=0.3,
            )
        )
        return {"evidences": {"vision_analysis": evidences}}

    # Use multimodal LLM to classify diagrams.
    llm_instance = get_llm()
    analyses: List[Dict[str, Any]] = []

    instruction = (
        "You are a multimodal software architecture analyst.\n"
        "You will be shown a single image from a technical report.\n"
        "Determine whether the image is most likely:\n"
        "- a LangGraph-style StateGraph diagram (nodes and edges for stateful workflows),\n"
        "- a generic box or flow diagram,\n"
        "- or something else entirely.\n\n"
        "Respond with STRICT JSON for this image only:\n"
        '{\n'
        '  \"diagram_type\": \"stategraph\" | \"generic\" | \"other\",\n'
        '  \"reason\": \"brief explanation\",\n'
        '  \"confidence\": 0.0-1.0\n'
        '}\n"
    )

    for idx, img_bytes in enumerate(images[:5]):  # Safety: limit number of images
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        message = HumanMessage(
            content=[
                {"type": "text", "text": instruction},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                },
            ]
        )

        try:
            response = llm_instance.invoke([message])
            raw_content = getattr(response, "content", response)
            try:
                parsed = json.loads(raw_content)
            except Exception:
                parsed = {"raw_response": raw_content}

            analyses.append(
                {
                    "image_index": idx,
                    "analysis": parsed,
                }
            )
        except Exception as e:
            analyses.append(
                {
                    "image_index": idx,
                    "error": str(e),
                }
            )

    evidence = Evidence(
        goal="Visual Diagram Analysis",
        found=True,
        content={
            "pdf_path": pdf_path,
            "images_analyzed": len(analyses),
            "analyses": analyses,
        },
        location=pdf_path,
        rationale="Analyzed extracted PDF images with a multimodal LLM to distinguish StateGraph diagrams from generic diagrams.",
        confidence=0.7,
    )
    evidences.append(evidence)

    return {"evidences": {"vision_analysis": evidences}}
