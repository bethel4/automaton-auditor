# src/tools/repo_tools.py

import os
import subprocess
import tempfile
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


def clone_repository(repo_url: str) -> Tuple[Path, tempfile.TemporaryDirectory]:
    """
    Safely clone a repository into a temporary directory.
    
    Returns:
        Tuple of (repo_path, temp_dir) - caller must clean up temp_dir
    """
    temp_dir = tempfile.TemporaryDirectory()
    repo_path = Path(temp_dir.name)
    
    try:
        # Use subprocess, NOT os.system
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown git error"
            raise Exception(f"Git clone failed: {error_msg}")
        
        return repo_path, temp_dir
        
    except Exception as e:
        temp_dir.cleanup()
        raise e


def extract_git_history(repo_path: Path, max_commits: int = 50) -> List[Dict[str, Any]]:
    """
    Extract git commit history deterministically.
    
    Returns:
        List of commits with hash, message, author, date
    """
    try:
        # Get commit history in reverse chronological order
        result = subprocess.run(
            ["git", "log", f"--max-count={max_commits}", "--pretty=format:%h|%s|%an|%at"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        
        if result.returncode != 0:
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line or '|' not in line:
                continue
            parts = line.split('|', 3)
            if len(parts) == 4:
                hash_val, msg, author, timestamp = parts
                commits.append({
                    "hash": hash_val,
                    "message": msg,
                    "author": author,
                    "timestamp": int(timestamp) if timestamp.isdigit() else 0,
                    "datetime": datetime.fromtimestamp(int(timestamp)).isoformat() if timestamp.isdigit() else "unknown"
                })
        
        return commits
        
    except Exception as e:
        return []


def analyze_commit_patterns(commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic analysis of commit patterns - NO LLM
    
    Returns:
        Dict with pattern analysis results
    """
    if not commits or len(commits) == 0:
        return {
            "total_commits": 0,
            "bulk_upload_detected": True,
            "has_setup_commits": False,
            "has_tool_commits": False,
            "has_graph_commits": False,
            "has_test_commits": False,
            "has_doc_commits": False,
            "progression_score": 1,
            "commit_frequency": "unknown",
            "is_atomic": False
        }
    
    # Check commit messages for keywords
    all_messages = " ".join([c.get("message", "").lower() for c in commits])
    
    has_setup = any(k in all_messages for k in ["setup", "init", "initial", "environment", "bootstrap"])
    has_tool = any(k in all_messages for k in ["tool", "util", "helper", "function", "feature"])
    has_graph = any(k in all_messages for k in ["graph", "node", "edge", "langgraph", "state", "agent"])
    has_test = any(k in all_messages for k in ["test", "spec", "unit", "integration"])
    has_doc = any(k in all_messages for k in ["doc", "readme", "comment", "explain"])
    
    # Detect bulk upload (single commit with everything)
    bulk_upload = len(commits) <= 2
    
    # Check if commits are spread out over time
    timestamps = [c.get("timestamp", 0) for c in commits if c.get("timestamp", 0) > 0]
    time_spread = False
    if len(timestamps) >= 2:
        time_diff = max(timestamps) - min(timestamps)
        time_spread = time_diff > 3600  # More than 1 hour spread
    
    # Calculate progression score 1-5
    progression_score = 1
    if has_setup:
        progression_score += 1
    if has_tool:
        progression_score += 1
    if has_graph:
        progression_score += 1
    if has_test:
        progression_score += 1
    if len(commits) > 5:
        progression_score += 1
    
    return {
        "total_commits": len(commits),
        "bulk_upload_detected": bulk_upload,
        "has_setup_commits": has_setup,
        "has_tool_commits": has_tool,
        "has_graph_commits": has_graph,
        "has_test_commits": has_test,
        "has_doc_commits": has_doc,
        "progression_score": min(5, progression_score),
        "commit_frequency": "spread_out" if time_spread else "clustered",
        "is_atomic": len(commits) > 3 and time_spread,
        "meaningful_messages": sum(1 for c in commits if len(c.get("message", "")) > 10)
    }


def ast_parse_state_management(repo_path: Path) -> Dict[str, Any]:
    """
    Use AST to analyze state management code - NO LLM
    
    Returns:
        Dict with analysis results
    """
    state_file = repo_path / "src" / "state.py"
    if not state_file.exists():
        return {
            "exists": False,
            "has_pydantic": False,
            "has_reducers": False,
            "evidence_class": False,
            "judicial_opinion_class": False,
            "audit_report_class": False,
            "has_annotated": False,
            "file_path": "src/state.py"
        }
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        has_pydantic = False
        has_reducers = False
        has_annotated = False
        evidence_class = False
        judicial_opinion_class = False
        audit_report_class = False
        
        for node in ast.walk(tree):
            # Check for BaseModel inheritance
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BaseModel":
                        has_pydantic = True
                        if node.name == "Evidence":
                            evidence_class = True
                        elif node.name == "JudicialOpinion":
                            judicial_opinion_class = True
                        elif node.name == "AuditReport":
                            audit_report_class = True
            
            # Check for Annotated and reducers
            if isinstance(node, ast.Subscript):
                try:
                    node_str = ast.unparse(node)
                    if "Annotated" in node_str:
                        has_annotated = True
                        if "operator.add" in node_str or "operator.ior" in node_str:
                            has_reducers = True
                except:
                    pass
        
        return {
            "exists": True,
            "has_pydantic": has_pydantic,
            "has_reducers": has_reducers,
            "has_annotated": has_annotated,
            "evidence_class": evidence_class,
            "judicial_opinion_class": judicial_opinion_class,
            "audit_report_class": audit_report_class,
            "file_path": "src/state.py"
        }
        
    except Exception as e:
        return {
            "exists": True,
            "error": str(e),
            "has_pydantic": False,
            "has_reducers": False,
            "file_path": "src/state.py"
        }


def ast_parse_graph_structure(repo_path: Path) -> Dict[str, Any]:
    """
    Use AST to analyze graph structure for parallelism - NO LLM
    
    Returns:
        Dict with parallelism analysis
    """
    graph_file = repo_path / "src" / "graph.py"
    if not graph_file.exists():
        return {
            "exists": False,
            "has_stategraph": False,
            "has_parallel_detectives": False,
            "has_parallel_judges": False,
            "has_aggregator": False,
            "has_add_edge": False,
            "graph_type": "missing"
        }
    
    try:
        with open(graph_file, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Look for StateGraph
        has_stategraph = "StateGraph" in content
        
        # Look for parallel patterns
        has_add_edge = "add_edge" in content
        
        # Check for multiple edges from same node (parallel fan-out)
        edge_calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr'):
                if node.func.attr == 'add_edge':
                    if len(node.args) >= 2:
                        try:
                            from_node = ast.unparse(node.args[0])
                            edge_calls.append(from_node)
                        except:
                            pass
        
        # Detect if multiple edges from same source (parallel fan-out)
        from collections import Counter
        edge_counts = Counter(edge_calls)
        has_parallel_fanout = any(count > 1 for count in edge_counts.values())
        
        # Check for aggregator
        has_aggregator = "aggregator" in content.lower() or "evidence_aggregator" in content.lower()
        
        # Check for judges
        has_prosecutor = "prosecutor" in content.lower()
        has_defense = "defense" in content.lower()
        has_tech_lead = "tech_lead" in content.lower() or "techlead" in content.lower()
        
        return {
            "exists": True,
            "has_stategraph": has_stategraph,
            "has_add_edge": has_add_edge,
            "has_parallel_fanout": has_parallel_fanout,
            "has_aggregator": has_aggregator,
            "has_prosecutor": has_prosecutor,
            "has_defense": has_defense,
            "has_tech_lead": has_tech_lead,
            "file_path": "src/graph.py",
            "graph_type": "parallel" if has_parallel_fanout else "linear"
        }
        
    except Exception as e:
        return {
            "exists": True,
            "error": str(e),
            "has_stategraph": False,
            "file_path": "src/graph.py"
        }


def check_tool_safety(repo_path: Path) -> Dict[str, Any]:
    """
    Check for safe tooling practices - NO LLM
    
    Returns:
        Dict with safety analysis
    """
    tools_dir = repo_path / "src" / "tools"
    if not tools_dir.exists():
        return {
            "has_tempfile": False,
            "has_os_system": False,
            "has_subprocess": False,
            "has_error_handling": False,
            "safety_score": 1,
            "unsafe_calls": []
        }
    
    has_tempfile = False
    has_os_system = False
    has_subprocess = False
    has_error_handling = False
    unsafe_calls = []
    
    for py_file in tools_dir.glob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                
                # Check for tempfile
                if "tempfile.TemporaryDirectory" in content:
                    has_tempfile = True
                
                # Check for os.system (unsafe)
                if "os.system" in content:
                    has_os_system = True
                    unsafe_calls.append(f"{py_file.name}: os.system")
                
                # Check for subprocess
                if "subprocess.run" in content or "subprocess.Popen" in content:
                    has_subprocess = True
                
                # Check for try/except blocks
                for node in ast.walk(tree):
                    if isinstance(node, ast.Try):
                        has_error_handling = True
        except:
            continue
    
    # Calculate safety score (1-5)
    safety_score = 1
    if has_tempfile:
        safety_score += 1
    if has_subprocess and not has_os_system:
        safety_score += 2
    if has_error_handling:
        safety_score += 1
    if has_os_system:
        safety_score -= 1  # Penalty for os.system
    
    return {
        "has_tempfile": has_tempfile,
        "has_os_system": has_os_system,
        "has_subprocess": has_subprocess,
        "has_error_handling": has_error_handling,
        "safety_score": max(1, min(5, safety_score)),
        "unsafe_calls": unsafe_calls
    }


def check_structured_output(repo_path: Path) -> Dict[str, Any]:
    """
    Check for structured output usage in judges - NO LLM
    
    Returns:
        Dict with structured output analysis
    """
    judges_file = repo_path / "src" / "nodes" / "judges.py"
    if not judges_file.exists():
        return {
            "has_structured_output": False,
            "uses_pydantic": False,
            "has_with_structured_output": False,
            "structured_output_score": 1
        }
    
    try:
        with open(judges_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_structured = "with_structured_output" in content
        uses_pydantic = "JudicialOpinion" in content
        has_retry = "try:" in content or "except" in content
        
        score = 1
        if has_structured:
            score += 2
        if uses_pydantic:
            score += 2
        if has_retry:
            score += 1
        
        return {
            "has_structured_output": has_structured,
            "uses_pydantic": uses_pydantic,
            "has_retry_logic": has_retry,
            "structured_output_score": min(5, score)
        }
        
    except Exception as e:
        return {
            "has_structured_output": False,
            "uses_pydantic": False,
            "error": str(e),
            "structured_output_score": 1
        }


def get_repo_files(repo_path: Path) -> List[str]:
    """Get list of all Python files in repo"""
    files = []
    for py_file in repo_path.glob("**/*.py"):
        relative = str(py_file.relative_to(repo_path))
        files.append(relative)
    return files