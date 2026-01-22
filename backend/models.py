# backend/models.py
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field

# --- 1. Pydantic Models (For LLM Structured Output) ---


class Issue(BaseModel):
    id: str = Field(description="Unique ID for the issue (e.g., '1', '2').")

    severity: str = Field(
        description="Severity level: 'High' (Critical/Missing Data), 'Medium' (Partial/Wrong Context), or 'Low' (Formatting/Style)."
    )

    issue_description: str = Field(
        description="A concise explanation of the gap between the User Content and the Criteria."
    )

    recommendation: str = Field(
        description="Specific advice. If data is missing, tell the user exactly what value to input."
    )

    fixable: bool = Field(
        description=(
            "CRITICAL: Set to True ONLY if the AI can fix this issue by reformatting or moving existing text. "
            "Set to False if the issue is caused by MISSING INFORMATION (e.g., empty placeholders like <Add Name>, blank fields) "
            "that the user must provide manually."
        )
    )


class AuditResponse(BaseModel):
    is_compliant: bool = Field(
        description="True only if the content fully meets all Criteria and matches the Template Structure requirements."
    )
    issues: List[Issue] = Field(default=[], description="List of identified issues.")


class GlobalIssue(BaseModel):
    id: str = Field(description="Unique ID for the logic issue (e.g., 'G-1').")
    
    title: str = Field(
        description="Short title of the logic mismatch (e.g., 'Solution contradicts Problem')."
    )
    
    description: str = Field(
        description="Detailed explanation of the logical inconsistency found across sections."
    )
    
    related_sections: List[str] = Field(
        description="List of section names that are involved in this conflict."
    )


class ConsistencyResponse(BaseModel):
    is_consistent: bool = Field(
        description="True if the document is logically consistent across all sections."
    )
    global_issues: List[GlobalIssue] = Field(default=[], description="List of logical inconsistencies found.")


class FixResponse(BaseModel):
    fixed_content: str = Field(
        description="The rewritten content. It must follow the Template Structure but contain the User's original data."
    )


# --- 2. LangGraph State (Context Management) ---


class AgentState(TypedDict):
    # --- Inputs (Read Only) ---
    section_title: str
    criteria: str  # The detailed instructions (e.g., "Must include Q-PAR")
    template_structure: str  # The strict format (e.g., "Reviewers: <Name>")

    # --- User Data (Read/Write) ---
    user_content: str  # The actual text written by the user

    # --- Outputs (Written by Auditor) ---
    issues: List[dict]  # Serialized Issue objects
    is_compliant: bool

    # --- Triggers (Written by Frontend) ---
    target_issue: Optional[dict]  # The specific issue the user wants to Auto-Fix
