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
    Safely clone a repository into a temporary directory with enhanced error handling.
    
    Args:
        repo_url: URL of the repository to clone
        
    Returns:
        Tuple of (repo_path, temp_dir) - caller must clean up temp_dir
        
    Raises:
        Exception: If clone fails with detailed error information
    """
    print(f"🔄 Starting git clone for: {repo_url}")
    temp_dir = tempfile.TemporaryDirectory()
    repo_path = Path(temp_dir.name)
    
    try:
        # Validate URL format
        if not repo_url.startswith(('http://', 'https://', 'git@')):
            raise Exception(f"Invalid repository URL format: {repo_url}")
        
        print(f"📁 Creating temporary directory: {repo_path}")
        # Use subprocess with enhanced safety
        print(f"🔄 Executing: git clone {repo_url} {repo_path}")
        result = subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )
        
        print(f"🔄 Git clone completed with return code: {result.returncode}")
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown git error"
            print(f"❌ Git clone error: {error_msg}")
            
            # Handle common authentication errors
            if "authentication failed" in error_msg.lower():
                raise Exception(f"Authentication failed for repository {repo_url}. Please check credentials or repository access.")
            elif "not found" in error_msg.lower():
                raise Exception(f"Repository not found: {repo_url}. Please check the URL.")
            elif "permission denied" in error_msg.lower():
                raise Exception(f"Permission denied for repository {repo_url}. Repository may be private.")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                raise Exception(f"Network error cloning repository {repo_url}: {error_msg}")
            else:
                raise Exception(f"Git clone failed for {repo_url}: {error_msg}")
        
        # Verify the clone was successful
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            raise Exception(f"Clone appeared successful but .git directory not found in {repo_path}")
        
        print(f"✅ Repository successfully cloned to: {repo_path}")
        return repo_path, temp_dir
        
    except subprocess.TimeoutExpired:
        print(f"❌ Git clone timed out after 300 seconds")
        raise Exception(f"Git clone timed out after 300 seconds for repository: {repo_url}")
    except Exception as e:
        print(f"❌ Clone failed: {str(e)}")
        # Clean up temp directory on failure
        try:
            temp_dir.cleanup()
        except:
            pass
        raise


def extract_git_history(repo_path: Path, max_commits: int = 50) -> Dict[str, Any]:
    """
    Extract git commit history deterministically with enhanced safety and error handling.
    
    Args:
        repo_path: Path to the git repository
        max_commits: Maximum number of commits to extract
        
    Returns:
        Dict with commit history and metadata
    """
    try:
        # Verify this is a git repository
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            return {
                "exists": False,
                "commits": [],
                "total_commits": 0,
                "error": "Not a git repository",
                "repo_path": str(repo_path)
            }
        
        # Get commit history with full details
        result = subprocess.run(
            ["git", "log", f"--max-count={max_commits}", "--pretty=format:%h|%s|%an|%ae|%at|%ci"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown git error"
            return {
                "exists": True,
                "commits": [],
                "total_commits": 0,
                "error": f"Git log failed: {error_msg}",
                "repo_path": str(repo_path)
            }
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) >= 6:  # We expect at least 6 parts
                commit_hash = parts[0]
                subject = parts[1]
                author = parts[2]
                email = parts[3]
                timestamp = parts[4]
                date = parts[5]
                
                commits.append({
                    "hash": commit_hash,
                    "subject": subject,
                    "author": author,
                    "email": email,
                    "date": date,
                    "timestamp": timestamp
                })
        
        # Get total commit count
        total_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        total_commits = 0
        if total_result.returncode == 0:
            try:
                total_commits = int(total_result.stdout.strip())
            except ValueError:
                total_commits = len(commits)
        else:
            total_commits = len(commits)
        
        # Get repository info
        remote_result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        
        remotes = []
        if remote_result.returncode == 0:
            for line in remote_result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) == 2:
                        name, url = parts
                        remotes.append({"name": name, "url": url.split()[0] if url else ""})
        
        return {
            "exists": True,
            "commits": commits,
            "total_commits": total_commits,
            "extracted_commits": len(commits),
            "remotes": remotes,
            "error": None,
            "repo_path": str(repo_path)
        }
        
    except subprocess.TimeoutExpired:
        return {
            "exists": True,
            "commits": [],
            "total_commits": 0,
            "error": "Git operation timed out",
            "repo_path": str(repo_path)
        }
    except Exception as e:
        return {
            "exists": True,
            "commits": [],
            "total_commits": 0,
            "error": f"Error extracting git history: {str(e)}",
            "repo_path": str(repo_path)
        }


def analyze_commit_patterns(git_history: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic analysis of commit patterns - NO LLM
    
    Args:
        git_history: Dict returned by extract_git_history
        
    Returns:
        Dict with pattern analysis results
    """
    commits = git_history.get("commits", [])
    
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
    all_messages = " ".join([c.get("subject", "").lower() for c in commits])
    
    has_setup = any(k in all_messages for k in ["setup", "init", "initial", "environment", "bootstrap"])
    has_tool = any(k in all_messages for k in ["tool", "util", "helper", "function", "feature"])
    has_graph = any(k in all_messages for k in ["graph", "node", "edge", "langgraph", "state", "agent"])
    has_test = any(k in all_messages for k in ["test", "spec", "unit", "integration"])
    has_doc = any(k in all_messages for k in ["doc", "readme", "comment", "explain"])
    
    # Detect bulk upload (single commit with everything)
    bulk_upload = len(commits) <= 2
    
    # Check if commits are spread out over time
    timestamps = []
    for c in commits:
        try:
            ts = int(c.get("timestamp", 0))
            if ts > 0:
                timestamps.append(ts)
        except (ValueError, TypeError):
            pass
    
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
        "meaningful_messages": sum(1 for c in commits if len(c.get("subject", "")) > 10)
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
    Use robust AST to analyze graph structure for parallelism - NO LLM
    
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
            "graph_type": "missing",
            "stategraph_instantiations": [],
            "parallel_patterns": [],
            "error": None
        }
    
    try:
        with open(graph_file, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Robust StateGraph detection using AST
        stategraph_imports = []
        stategraph_instantiations = []
        variable_names = set()
        
        # Track imports and variable names
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "langgraph.graph":
                        stategraph_imports.append("langgraph.graph")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "langgraph.graph":
                    for alias in node.names:
                        if alias.name == "StateGraph":
                            stategraph_imports.append("langgraph.graph.StateGraph")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variable_names.add(target.id)
            elif isinstance(node, ast.Call):
                # Check for StateGraph instantiation
                if isinstance(node.func, ast.Name) and node.func.id == "StateGraph":
                    stategraph_instantiations.append("StateGraph()")
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr == "StateGraph":
                        func_str = ast.unparse(node.func)
                        stategraph_instantiations.append(f"{func_str}()")
        
        has_stategraph = len(stategraph_imports) > 0 and len(stategraph_instantiations) > 0
        
        # Robust parallel pattern detection
        edge_calls = []
        conditional_edges = []
        parallel_patterns = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check for add_edge calls
                    if node.func.attr == 'add_edge':
                        if len(node.args) >= 2:
                            try:
                                from_node = ast.unparse(node.args[0])
                                to_node = ast.unparse(node.args[1])
                                edge_calls.append((from_node, to_node))
                            except:
                                pass
                    
                    # Check for add_conditional_edges
                    elif node.func.attr == 'add_conditional_edges':
                        if len(node.args) >= 2:
                            try:
                                from_node = ast.unparse(node.args[0])
                                conditional_edges.append(from_node)
                            except:
                                pass
        
        # Detect parallel patterns
        from collections import Counter
        edge_sources = [source for source, _ in edge_calls]
        edge_counts = Counter(edge_sources)
        
        has_parallel_fanout = any(count > 1 for count in edge_counts.values())
        has_parallel_judges = any("judge" in source.lower() and count > 1 for source, count in edge_counts.items())
        has_parallel_detectives = any("detective" in source.lower() and count > 1 for source, count in edge_counts.items())
        
        if has_parallel_fanout:
            parallel_patterns.append("parallel_fan_out")
        if has_parallel_judges:
            parallel_patterns.append("parallel_judges")
        if has_parallel_detectives:
            parallel_patterns.append("parallel_detectives")
        if conditional_edges:
            parallel_patterns.append("conditional_routing")
        
        # Check for aggregator using AST
        has_aggregator = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if "aggregator" in node.id.lower() or "evidence_aggregator" in node.id.lower():
                    has_aggregator = True
                    break
            elif isinstance(node, ast.Attribute):
                if "aggregator" in node.attr.lower():
                    has_aggregator = True
                    break
        
        has_add_edge = len(edge_calls) > 0
        
        # Determine graph type
        if not has_stategraph:
            graph_type = "no_langgraph"
        elif has_parallel_fanout:
            graph_type = "parallel"
        elif has_add_edge:
            graph_type = "sequential"
        else:
            graph_type = "minimal"
        
        return {
            "exists": True,
            "has_stategraph": has_stategraph,
            "has_parallel_detectives": has_parallel_detectives,
            "has_parallel_judges": has_parallel_judges,
            "has_aggregator": has_aggregator,
            "has_add_edge": has_add_edge,
            "graph_type": graph_type,
            "stategraph_instantiations": stategraph_instantiations,
            "parallel_patterns": parallel_patterns,
            "edge_count": len(edge_calls),
            "conditional_edge_count": len(conditional_edges),
            "error": None
        }
        
    except SyntaxError as e:
        return {
            "exists": True,
            "has_stategraph": False,
            "has_parallel_detectives": False,
            "has_parallel_judges": False,
            "has_aggregator": False,
            "has_add_edge": False,
            "graph_type": "syntax_error",
            "stategraph_instantiations": [],
            "parallel_patterns": [],
            "error": f"Syntax error in graph.py: {str(e)}"
        }
    except Exception as e:
        return {
            "exists": True,
            "has_stategraph": False,
            "has_parallel_detectives": False,
            "has_parallel_judges": False,
            "has_aggregator": False,
            "has_add_edge": False,
            "graph_type": "error",
            "stategraph_instantiations": [],
            "parallel_patterns": [],
            "error": f"Error analyzing graph.py: {str(e)}"
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