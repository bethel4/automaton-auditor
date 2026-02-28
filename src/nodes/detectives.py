# src/nodes/detectives.py

import os
import json
from typing import Dict, Any, List
from pathlib import Path

from src.state import AgentState, Evidence
from src.tools import repo_tools, doc_tools, vision_tools
from src.utils.rubric_loader import load_rubric, ContextBuilder
from src.llm_router import get_llm_for_task, get_fallback_llm, DEBUG_MODE


def repo_investigator(state: AgentState) -> Dict[str, Any]:
    """
    Detective: Git forensic analysis with deterministic tools + LLM interpretation
    
    Workflow:
    1. Clone repo safely
    2. Run deterministic tools to collect facts
    3. Use LLM to interpret patterns (not to generate facts)
    4. Store both facts and interpretation as Evidence
    """
    repo_url = state["repo_url"]
    evidences = []
    errors = []
    
    # Load rubric instructions
    rubric_loader = state["config"]["rubric"]
    repo_dimensions = rubric_loader.get_repo_detective_instructions()
    
    repo_path = None
    temp_dir = None
    
    try:
        # --- STEP 1: SAFELY CLONE REPOSITORY ---
        repo_path, temp_dir = repo_tools.clone_repository(repo_url)
        
        # --- STEP 2: DETERMINISTIC FORENSICS (NO LLM) ---
        
        # Get git history
        commits = repo_tools.extract_git_history(repo_path)
        
        # Deterministic commit pattern analysis
        commit_analysis = repo_tools.analyze_commit_patterns(commits)
        
        # AST analysis of state management
        state_analysis = repo_tools.ast_parse_state_management(repo_path)
        
        # AST analysis of graph structure
        graph_analysis = repo_tools.ast_parse_graph_structure(repo_path)
        
        # Check tool safety
        safety_analysis = repo_tools.check_tool_safety(repo_path)
        
        # Check structured output
        structured_analysis = repo_tools.check_structured_output(repo_path)
        
        # Get all repo files for cross-reference
        repo_files = repo_tools.get_repo_files(repo_path)
        
        # --- STEP 3: STORE DETERMINISTIC EVIDENCE FIRST ---
        
        # Git history evidence (deterministic)
        evidences.append(Evidence(
            goal="Git Forensic Analysis",
            found=True,
            content={
                "commit_count": len(commits),
                "analysis": commit_analysis,
                "sample_commits": commits[:5] if commits else []
            },
            location=repo_url,
            rationale=f"Found {len(commits)} commits. Progression score: {commit_analysis.get('progression_score', 1)}/5",
            confidence=0.95,
            evidence_type="deterministic"
        ))
        
        # State management evidence (deterministic)
        evidences.append(Evidence(
            goal="State Management Rigor",
            found=state_analysis.get("exists", False),
            content=state_analysis,
            location="src/state.py",
            rationale=f"Pydantic models: {state_analysis.get('has_pydantic', False)}, Reducers: {state_analysis.get('has_reducers', False)}",
            confidence=0.95,
            evidence_type="deterministic"
        ))
        
        # Graph orchestration evidence (deterministic)
        evidences.append(Evidence(
            goal="Graph Orchestration Architecture",
            found=graph_analysis.get("exists", False),
            content=graph_analysis,
            location="src/graph.py",
            rationale=f"Has StateGraph: {graph_analysis.get('has_stategraph', False)}, Parallel: {graph_analysis.get('has_parallel_keyword', False)}",
            confidence=0.9,
            evidence_type="deterministic"
        ))
        
        # Safe tool engineering evidence (deterministic)
        evidences.append(Evidence(
            goal="Safe Tool Engineering",
            found=True,
            content=safety_analysis,
            location="src/tools/",
            rationale=f"Safety score: {safety_analysis.get('safety_score', 1)}/5",
            confidence=0.95,
            evidence_type="deterministic"
        ))
        
        # Structured output enforcement (deterministic)
        evidences.append(Evidence(
            goal="Structured Output Enforcement",
            found=structured_analysis.get("has_structured_output", False),
            content=structured_analysis,
            location="src/nodes/judges.py",
            rationale=f"Structured output: {structured_analysis.get('has_structured_output', False)}",
            confidence=0.95,
            evidence_type="deterministic"
        ))
        
        # --- STEP 4: LLM INTERPRETATION (ONLY AFTER FACTS) ---
        
        # Create FACT PACKAGE for LLM (no raw data, only structured facts)
        fact_package = {
            "commit_stats": commit_analysis,
            "state_management": state_analysis,
            "graph_structure": graph_analysis,
            "safety": safety_analysis,
            "structured_output": structured_analysis,
            "total_files": len(repo_files),
            "has_state_file": state_analysis.get("exists", False),
            "has_graph_file": graph_analysis.get("exists", False)
        }
        
        # Use LLM ONLY to interpret patterns
        try:
            llm = get_llm_for_task("detective")
            
            interpretation_prompt = f"""
You are a forensic software analyst. Below are DETERMINISTIC FACTS collected from a repository.
Based SOLELY on these facts, provide your professional interpretation.

FACTS:
{json.dumps(fact_package, indent=2)}

Answer in JSON format:
{{
    "development_pattern": "disciplined|messy|bulk_upload|iterative",
    "architectural_understanding": "low|medium|high",
    "security_consciousness": "low|medium|high",
    "confidence": 0.0-1.0,
    "key_observations": ["observation1", "observation2"]
}}
"""
            
            response = llm.invoke(interpretation_prompt)
            
            # Parse JSON response
            if hasattr(response, 'content'):
                interpretation = json.loads(response.content)
            else:
                interpretation = json.loads(response)
            
            # Store interpretation as evidence (lower confidence)
            evidences.append(Evidence(
                goal="Developer Pattern Analysis",
                found=True,
                content=interpretation,
                location=repo_url,
                rationale=f"Pattern: {interpretation.get('development_pattern', 'unknown')}",
                confidence=interpretation.get('confidence', 0.7),
                evidence_type="llm_interpretation"
            ))
            
        except Exception as e:
            errors.append(f"LLM interpretation failed: {str(e)}")
            # No LLM interpretation, but we still have deterministic evidence
        
        # --- STEP 5: JUDICIAL NUANCE CHECK (deterministic) ---
        # Check if judge personas are distinct
        judges_file = repo_path / "src" / "nodes" / "judges.py"
        if judges_file.exists():
            with open(judges_file) as f:
                judges_content = f.read()
            
            has_prosecutor = "Prosecutor" in judges_content
            has_defense = "Defense" in judges_content
            has_tech_lead = "TechLead" in judges_content
            
            evidences.append(Evidence(
                goal="Judicial Nuance and Dialectics",
                found=has_prosecutor and has_defense and has_tech_lead,
                content={
                    "has_prosecutor": has_prosecutor,
                    "has_defense": has_defense,
                    "has_tech_lead": has_tech_lead
                },
                location="src/nodes/judges.py",
                rationale=f"Found all three personas: {has_prosecutor and has_defense and has_tech_lead}",
                confidence=0.9,
                evidence_type="deterministic"
            ))
        
        return {
            "evidences": {"repo_investigator": evidences},
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"RepoInvestigator failed: {str(e)}")
        error_evidence = Evidence(
            goal="Repository Analysis",
            found=False,
            content=f"Analysis failed: {str(e)}",
            location=repo_url,
            rationale=f"Failed to analyze repository: {str(e)}",
            confidence=0.1,
            evidence_type="deterministic"
        )
        
        return {
            "evidences": {"repo_investigator": [error_evidence]},
            "errors": errors
        }
        
    finally:
        # Clean up temp directory
        if temp_dir:
            temp_dir.cleanup()


def doc_analyst(state: AgentState) -> Dict[str, Any]:
    """Detective: PDF analysis with deterministic extraction + LLM interpretation"""
    pdf_path = state.get("pdf_path", "")
    evidences = []
    errors = []
    
    if not pdf_path or not os.path.exists(pdf_path):
        evidences.append(Evidence(
            goal="PDF Report Analysis",
            found=False,
            content=None,
            location=pdf_path,
            rationale="PDF file not found",
            confidence=0.0,
            evidence_type="deterministic"
        ))
        return {"evidences": {"doc_analyst": evidences}, "errors": errors}
    
    try:
        # --- STEP 1: DETERMINISTIC EXTRACTION ---
        
        # Extract text from PDF
        pdf_text = doc_tools.extract_text_from_pdf(pdf_path)
        
        # Extract file paths mentioned
        claimed_paths = doc_tools.extract_file_paths_from_text(pdf_text)
        
        # Check for key concepts
        concepts = doc_tools.extract_concepts(pdf_text)
        
        # Get metadata
        metadata = doc_tools.extract_metadata(pdf_text)
        
        # Chunk text for LLM
        chunks = doc_tools.chunk_text(pdf_text, chunk_size=3000)
        
        # --- STEP 2: CROSS-REFERENCE WITH REPO (if available) ---
        cross_reference = {"verified": [], "hallucinated": []}
        
        # Check if we have repo files from other detectives
        if "repo_investigator" in state.get("evidences", {}):
            repo_evidence = state["evidences"]["repo_investigator"]
            for ev in repo_evidence:
                if ev.goal == "Repository Files":
                    repo_files = ev.content
                    cross_reference = doc_tools.cross_reference_paths(claimed_paths, repo_files)
        
        # --- STEP 3: STORE DETERMINISTIC EVIDENCE ---
        
        evidences.append(Evidence(
            goal="Report Accuracy (Cross-Reference)",
            found=len(cross_reference.get("verified", [])) > 0,
            content={
                "claimed_paths": claimed_paths[:10],
                "verified": cross_reference.get("verified", [])[:10],
                "hallucinated": cross_reference.get("hallucinated", [])[:10]
            },
            location=pdf_path,
            rationale=f"Verified {len(cross_reference.get('verified', []))} paths, hallucinated {len(cross_reference.get('hallucinated', []))}",
            confidence=0.9,
            evidence_type="deterministic"
        ))
        
        evidences.append(Evidence(
            goal="Theoretical Depth",
            found=any(concepts.values()),
            content=concepts,
            location=pdf_path,
            rationale=f"Found concepts: {[k for k,v in concepts.items() if v]}",
            confidence=0.85,
            evidence_type="deterministic"
        ))
        
        # --- STEP 4: LLM INTERPRETATION FOR DEPTH ---
        
        if chunks:
            try:
                llm = get_llm_for_task("detective")
                
                depth_prompt = f"""
You are analyzing a technical PDF report. Here are excerpts:

{chunks[0][:2000]}  # First chunk for context

Based on this text, determine if the author demonstrates DEEP UNDERSTANDING
or just uses buzzwords superficially.

Answer in JSON:
{{
    "understanding_depth": "shallow|moderate|deep",
    "buzzword_dropping": true|false,
    "substantive_explanations": ["concept1", "concept2"],
    "confidence": 0.0-1.0,
    "summary": "brief assessment"
}}
"""
                
                response = llm.invoke(depth_prompt)
                
                if hasattr(response, 'content'):
                    depth_analysis = json.loads(response.content)
                else:
                    depth_analysis = json.loads(response)
                
                evidences.append(Evidence(
                    goal="Theoretical Depth Analysis",
                    found=True,
                    content=depth_analysis,
                    location=pdf_path,
                    rationale=f"Depth: {depth_analysis.get('understanding_depth', 'unknown')}",
                    confidence=depth_analysis.get('confidence', 0.7),
                    evidence_type="llm_interpretation"
                ))
                
            except Exception as e:
                errors.append(f"LLM depth analysis failed: {str(e)}")
        
        return {
            "evidences": {"doc_analyst": evidences},
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"DocAnalyst failed: {str(e)}")
        error_evidence = Evidence(
            goal="PDF Analysis",
            found=False,
            content={"error": str(e)},
            location=pdf_path,
            rationale=f"Failed to analyze PDF: {str(e)}",
            confidence=0.1,
            evidence_type="deterministic"
        )
        
        return {
            "evidences": {"doc_analyst": [error_evidence]},
            "errors": errors
        }


def vision_inspector(state: AgentState) -> Dict[str, Any]:
    """Detective: Multimodal diagram analysis (optional)"""
    pdf_path = state.get("pdf_path", "")
    evidences = []
    errors = []
    
    if not pdf_path or not os.path.exists(pdf_path):
        return {"evidences": {"vision_inspector": []}, "errors": errors}
    
    try:
        # Extract images from PDF
        images = doc_tools.extract_images_from_pdf(pdf_path)
        
        if not images:
            return {"evidences": {"vision_inspector": []}, "errors": errors}
        
        # Use vision LLM for analysis
        try:
            llm = get_llm_for_task("vision")
            
            # Analyze first few images
            analyses = []
            for i, img_bytes in enumerate(images[:3]):  # Limit to 3 images
                
                # For Ollama vision models, we need to handle image input
                # This is simplified - actual implementation depends on Ollama's vision API
                vision_prompt = f"""
Analyze this diagram image (image {i+1}).
Is this a LangGraph State Machine diagram, a generic flowchart, or something else?
Does it show parallel branches?

Return JSON:
{{
    "diagram_type": "stategraph|flowchart|other",
    "shows_parallelism": true|false,
    "confidence": 0.0-1.0,
    "description": "brief description"
}}
"""
                
                # In practice, you'd need to pass the image to Ollama
                # This is a placeholder - implement based on your Ollama vision setup
                analyses.append({
                    "image_index": i,
                    "diagram_type": "unknown",
                    "shows_parallelism": False,
                    "confidence": 0.5,
                    "description": "Vision analysis placeholder"
                })
            
            evidences.append(Evidence(
                goal="Architectural Diagram Analysis",
                found=True,
                content={"analyses": analyses, "total_images": len(images)},
                location=pdf_path,
                rationale=f"Analyzed {len(analyses)} images",
                confidence=0.7,
                evidence_type="llm_interpretation"
            ))
            
        except Exception as e:
            errors.append(f"Vision analysis failed: {str(e)}")
        
        return {
            "evidences": {"vision_inspector": evidences},
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"VisionInspector failed: {str(e)}")
        return {
            "evidences": {"vision_inspector": []},
            "errors": errors
        }