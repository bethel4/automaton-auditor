# src/nodes/detectives.py

from src.state import Evidence, AgentState
from src.tools.repo_tools import clone_repository, extract_git_history, analyze_graph_structure
from src.tools.doc_tools import ingest_pdf

from typing import Dict


def repo_investigator(state: AgentState) -> Dict:
    repo_url = state["repo_url"]

    try:
        repo_path = clone_repository(repo_url)
        commits = extract_git_history(repo_path)
        graph_analysis = analyze_graph_structure(repo_path)

        evidence = Evidence(
            goal="Git Forensic Analysis",
            found=len(commits) > 0,
            content="\n".join(commits[:5]),
            location=repo_url,
            rationale="Extracted git history successfully.",
            confidence=0.9,
        )

        return {"evidences": {"git_analysis": [evidence]}}

    except Exception as e:
        evidence = Evidence(
            goal="Git Forensic Analysis",
            found=False,
            content=None,
            location=repo_url,
            rationale=str(e),
            confidence=0.2,
        )

        return {"evidences": {"git_analysis": [evidence]}}


def doc_analyst(state: AgentState) -> Dict:
    pdf_path = state["pdf_path"]

    try:
        chunks = ingest_pdf(pdf_path)

        evidence = Evidence(
            goal="PDF Ingestion",
            found=len(chunks) > 0,
            content=f"{len(chunks)} chunks extracted",
            location=pdf_path,
            rationale="PDF successfully parsed.",
            confidence=0.9,
        )

        return {"evidences": {"pdf_analysis": [evidence]}}

    except Exception as e:
        evidence = Evidence(
            goal="PDF Ingestion",
            found=False,
            content=None,
            location=pdf_path,
            rationale=str(e),
            confidence=0.2,
        )

        return {"evidences": {"pdf_analysis": [evidence]}}