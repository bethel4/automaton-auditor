# src/tools/repo_tools.py

import subprocess
import tempfile
import os
import ast
import shutil
from typing import Dict, List, Optional

from gitingest import ingest as gitingest_ingest

# Global registry to keep temporary directories alive
_temp_dirs = []

def clone_repository(repo_url: str) -> str:
    """Clone repo into isolated temporary directory that persists."""
    # Create persistent temporary directory
    temp_dir = tempfile.mkdtemp(prefix="audit_repo_")
    _temp_dirs.append(temp_dir)  # Keep reference to prevent deletion

    print(f"Cloning {repo_url} to {temp_dir}")
    
    result = subprocess.run(
        ["git", "clone", repo_url, temp_dir],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )

    if result.returncode != 0:
        # Clean up on failure
        shutil.rmtree(temp_dir, ignore_errors=True)
        _temp_dirs.remove(temp_dir)
        raise RuntimeError(f"Git clone failed: {result.stderr}")

    print(f"Successfully cloned to {temp_dir}")
    return temp_dir

def cleanup_temp_dirs():
    """Clean up all temporary directories."""
    global _temp_dirs
    for temp_dir in _temp_dirs:
        shutil.rmtree(temp_dir, ignore_errors=True)
    _temp_dirs.clear()


def extract_git_history(repo_path: str) -> List[str]:
    """Extract commit history with error handling."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--reverse", "-50"],  # Limit to 50 commits
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to extract git history: {result.stderr}")

        commits = result.stdout.strip().split("\n")
        return [commit for commit in commits if commit.strip()]  # Filter empty lines
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git history extraction timed out")
    except Exception as e:
        raise RuntimeError(f"Failed to extract git history: {str(e)}")


def ingest_repository_with_gitingest(
    target: str,
    token: Optional[str] = None,
) -> Dict:
    """
    Use gitingest to produce a prompt-friendly digest of a repository.

    `target` can be a local path (e.g. the cloned repo_path) or a GitHub URL.
    This is read-only and does not execute any code from the target repo.
    """
    try:
        if token is not None:
            summary, tree, content = gitingest_ingest(target, token=token)
        else:
            summary, tree, content = gitingest_ingest(target)
    except Exception as e:
        # Surface a structured error but don't crash callers.
        return {
            "success": False,
            "error": str(e),
            "summary": "",
            "tree": "",
            "content": "",
        }

    return {
        "success": True,
        "summary": summary,
        "tree": tree,
        "content": content,
    }


def analyze_graph_structure(repo_path: str) -> Dict:
    """
    Parse Python files using AST to detect StateGraph usage with error handling.
    """
    findings = {
        "stategraph_found": False,
        "fan_out_detected": False,
        "files_analyzed": 0,
        "errors": []
    }

    try:
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    findings["files_analyzed"] += 1

                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            tree = ast.parse(content)
                    except SyntaxError as e:
                        findings["errors"].append(f"Syntax error in {full_path}: {str(e)}")
                        continue
                    except Exception as e:
                        findings["errors"].append(f"Error reading {full_path}: {str(e)}")
                        continue

                    # Look for StateGraph usage
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name) and node.id == "StateGraph":
                            findings["stategraph_found"] = True
                        
                        # Look for parallel patterns
                        if isinstance(node, ast.Call):
                            if (isinstance(node.func, ast.Attribute) and 
                                node.func.attr == "add_edge"):
                                # Check for multiple edges from same source (fan-out)
                                findings["fan_out_detected"] = True

    except Exception as e:
        findings["errors"].append(f"Analysis error: {str(e)}")

    return findings