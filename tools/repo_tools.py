# src/tools/repo_tools.py

import subprocess
import tempfile
import os
import ast
from typing import Dict, List


def clone_repository(repo_url: str) -> str:
    """Clone repo into isolated temporary directory."""
    temp_dir = tempfile.TemporaryDirectory()
    clone_path = temp_dir.name

    result = subprocess.run(
        ["git", "clone", repo_url, clone_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Git clone failed: {result.stderr}")

    return clone_path


def extract_git_history(repo_path: str) -> List[str]:
    """Extract commit history."""
    result = subprocess.run(
        ["git", "log", "--oneline", "--reverse"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError("Failed to extract git history")

    return result.stdout.strip().split("\n")


def analyze_graph_structure(repo_path: str) -> Dict:
    """
    Parse Python files using AST to detect StateGraph usage.
    """
    findings = {
        "stategraph_found": False,
        "fan_out_detected": False,
    }

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)

                with open(full_path, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read())
                    except Exception:
                        continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == "StateGraph":
                        findings["stategraph_found"] = True

    return findings