# src/state.py

import operator
from typing import Annotated, Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# --- Detective Output ---

class Evidence(BaseModel):
    goal: str = Field()
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[Any] = Field(default=None)
    location: str = Field(
        description="File path or commit hash",
    )
    rationale: str = Field(
        description="Your rationale for your confidence "
        "on the evidence you find for this particular goal",
    )
    confidence: float = Field(ge=0.0, le=1.0)

# --- Judge Output ---

class JudicialOpinion(BaseModel):
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str
    score: int = Field(ge=1, le=5)
    argument: str
    cited_evidence: List[str]

# --- Chief Justice Output ---

class CriterionResult(BaseModel):
    dimension_id: str
    name: str
    final_score: int = Field(ge=1, le=5)
    judge_opinions: List[JudicialOpinion]
    dissent_summary: Optional[str] = Field(
        default=None,
        description="Required when score variance > 2",
    )
    remediation: str = Field(
        description="Specific file-level instructions "
                    "for improvement",
    )

class AuditReport(BaseModel):
    repo_url: str
    executive_summary: str
    overall_score: float
    criteria: List[CriterionResult]
    remediation_plan: str

# --- Graph State ---

class AgentState(TypedDict):
    repo_url: str
    pdf_path: str
    config: Dict[str, Any]  # For rubric and other configuration
    rubric_dimensions: List[Dict]
    # Use reducers to prevent parallel agents
    # from overwriting data
    evidences: Annotated[
        Dict[str, List[Evidence]], operator.ior
    ]
    opinions: Annotated[
        List[JudicialOpinion], operator.add
    ]
    final_report: Optional[AuditReport]
    markdown_report: Optional[str]