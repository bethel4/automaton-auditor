# src/utils/rubric_loader.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# This module provides utilities for loading and handling the Week 2 rubric
# (as used by tests in this repository). It focuses on:
# - Loading the rubric JSON from a path or string
# - Parsing dimensions and extracting key instruction fields
# - Building agent-specific context and instructions based on target_artifact
# - Formatting criteria for judge prompts


Rubric = Dict[str, Any]
Dimension = Dict[str, Any]


def load_rubric(path: str | Path) -> Rubric:
    """
    Load rubric JSON from a file path.

    Parameters
    - path: str | Path to the rubric JSON file (e.g., ./rubric.json)

    Returns
    - Parsed rubric object as a dict
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_dimensions(rubric: Rubric) -> List[Dimension]:
    """
    Extract the list of dimensions from the rubric spec.

    The Week 2 rubric uses a top-level key 'dimensions' which is a list
    of dimension objects that include at least the following keys (by convention):
      - id / dimension_id
      - name
      - description
      - forensic_instruction (str)
      - judicial_logic (str)
      - synthesis_rules (str)
      - target_artifact (str or list[str]): which agent/artifact these apply to

    This function returns the raw dimension dictionaries for downstream processing.
    """
    dims = rubric.get("dimensions")
    if not isinstance(dims, list):
        return []
    return [d for d in dims if isinstance(d, dict)]


def extract_instructions(dimension: Dimension) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    From a dimension entry, extract the core instruction fields:
    - forensic_instruction
    - judicial_logic
    - synthesis_rules

    Returns a tuple (forensic_instruction, judicial_logic, synthesis_rules)
    with None for any missing field.
    """
    forensic = dimension.get("forensic_instruction")
    judicial = dimension.get("judicial_logic")
    synthesis = dimension.get("synthesis_rules")
    return (
        forensic if isinstance(forensic, str) else None,
        judicial if isinstance(judicial, str) else None,
        synthesis if isinstance(synthesis, str) else None,
    )


def get_target_artifacts(dimension: Dimension) -> List[str]:
    """
    Normalize the 'target_artifact' declaration for a dimension into a list of strings.
    Common values include: 'github_repo', 'pdf_report', 'pdf_images'.
    """
    target = dimension.get("target_artifact")
    if isinstance(target, str):
        return [target]
    if isinstance(target, list):
        return [t for t in target if isinstance(t, str)]
    return []


@dataclass
class InstructionBundle:
    dimension_id: Optional[str]
    name: Optional[str]
    target_artifacts: List[str]
    forensic_instruction: Optional[str]
    judicial_logic: Optional[str]
    synthesis_rules: Optional[str]
    raw: Dimension


def build_instruction_bundles(rubric: Rubric) -> List[InstructionBundle]:
    """
    Convert rubric dimensions to normalized InstructionBundle entries.
    """
    bundles: List[InstructionBundle] = []
    for d in parse_dimensions(rubric):
        forensic, judicial, synthesis = extract_instructions(d)
        bundles.append(
            InstructionBundle(
                dimension_id=(d.get("dimension_id") or d.get("id")) if isinstance(d.get("dimension_id") or d.get("id"), str) else None,
                name=d.get("name") if isinstance(d.get("name"), str) else None,
                target_artifacts=get_target_artifacts(d),
                forensic_instruction=forensic,
                judicial_logic=judicial,
                synthesis_rules=synthesis,
                raw=d,
            )
        )
    return bundles


class ContextBuilder:
    """
    Dispatch dimension instructions to appropriate agents based on target_artifact.

    Usage:
    - cb = ContextBuilder(rubric)
    - repo_detective_instr = cb.get_detective_instructions("github_repo")
    - pdf_detective_instr = cb.get_detective_instructions("pdf_report")
    - img_detective_instr = cb.get_detective_instructions("pdf_images")
    - judge_criteria_blocks = cb.format_criteria_for_judges()
    """

    def __init__(self, rubric: Rubric) -> None:
        self.rubric = rubric
        self.bundles = build_instruction_bundles(rubric)

    def dispatch_for_artifact(self, artifact: str) -> List[InstructionBundle]:
        """
        Return all bundles whose target_artifacts includes the given artifact.
        """
        return [b for b in self.bundles if artifact in b.target_artifacts]

    def get_detective_instructions(self, artifact: str) -> List[str]:
        """
        Get only the forensic instructions for a particular artifact.

        Common artifacts:
        - github_repo
        - pdf_report
        - pdf_images
        """
        out: List[str] = []
        for b in self.dispatch_for_artifact(artifact):
            if b.forensic_instruction:
                out.append(b.forensic_instruction)
        return out

    def get_repo_detective_instructions(self) -> List[str]:
        return self.get_detective_instructions("github_repo")

    def get_pdf_report_detective_instructions(self) -> List[str]:
        return self.get_detective_instructions("pdf_report")

    def get_pdf_images_detective_instructions(self) -> List[str]:
        return self.get_detective_instructions("pdf_images")

    # Judge helpers
    def format_criteria_for_judges(self) -> List[str]:
        """
        Return a list of formatted criterion blocks suitable for prompting judge agents.
        This uses each bundle's name, judicial_logic, and synthesis_rules.
        """
        blocks: List[str] = []
        for b in self.bundles:
            name = b.name or b.dimension_id or "Unnamed Criterion"
            jl = b.judicial_logic or ""
            sr = b.synthesis_rules or ""
            block = format_criterion_for_judge(name=name, judicial_logic=jl, synthesis_rules=sr)
            blocks.append(block)
        return blocks


# Standalone judge prompt formatting helpers

def format_criterion_for_judge(name: str, judicial_logic: str, synthesis_rules: str) -> str:
    """
    Create a prompt-ready criterion section for judges.
    """
    parts: List[str] = []
    parts.append(f"Criterion: {name}")
    if judicial_logic:
        parts.append("Judicial Logic:")
        parts.append(judicial_logic.strip())
    if synthesis_rules:
        parts.append("Synthesis Rules:")
        parts.append(synthesis_rules.strip())
    return "\n".join(parts).strip()


def format_all_criteria_for_judges(dimensions: Iterable[Dimension]) -> List[str]:
    """
    Format a collection of raw dimension dicts (already parsed) for judge prompts.
    """
    out: List[str] = []
    for d in dimensions:
        name = d.get("name") or d.get("dimension_id") or d.get("id") or "Unnamed Criterion"
        forensic, judicial, synthesis = extract_instructions(d)
        block = format_criterion_for_judge(name=str(name), judicial_logic=judicial or "", synthesis_rules=synthesis or "")
        out.append(block)
    return out


__all__ = [
    "Rubric",
    "Dimension",
    "load_rubric",
    "parse_dimensions",
    "extract_instructions",
    "get_target_artifacts",
    "InstructionBundle",
    "build_instruction_bundles",
    "ContextBuilder",
    "format_criterion_for_judge",
    "format_all_criteria_for_judges",
]
