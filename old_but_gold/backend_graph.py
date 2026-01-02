import os

import re

from typing import TypedDict, List, Optional

from dotenv import load_dotenv


from langchain_openai import ChatOpenAI

from langchain_core.messages import SystemMessage, HumanMessage

from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END

from langgraph.checkpoint.memory import MemorySaver


load_dotenv()


# --- 1. Data Models ---


class Issue(BaseModel):
    id: str = Field(description="Unique ID (e.g. 1, 2)")

    severity: str = Field(
        description="High (Critical missing info/placeholders), Medium (Partial info), or Low (Formatting)"
    )

    issue_description: str = Field(
        description="Explanation of why the content does not match the instruction."
    )

    recommendation: str = Field(description="Specific advice on what to add or change.")


class AuditResponse(BaseModel):
    is_compliant: bool = Field(
        description="True if the content fully meets the instructions."
    )

    issues: List[Issue] = Field(description="List of gaps found.")


class FixResponse(BaseModel):
    fixed_content: str = Field(
        description="The rewritten section content with the fix applied."
    )


class AgentState(TypedDict):
    # Core Data

    section_title: str

    document_text: str

    criteria: str

    # Audit Outputs

    issues: List[dict]

    is_compliant: bool

    # Fixer Inputs (Optional - only used when triggering a fix)

    target_issue: Optional[
        dict
    ]  # Contains {"issue_description": "...", "recommendation": "..."}


# --- 2. LLM Setup ---

llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
    temperature=0,
)


# --- 3. Nodes ---


def auditor_node(state: AgentState):
    """

    Compares the 'document_text' against the extracted 'criteria' (Instructions).

    Identifies gaps and unresolved placeholders.

    """

    print(f"--- Auditing Section: {state.get('section_title')} ---")

    doc = state.get("document_text", "")

    criteria = state.get("criteria", "")

    # 1. Quick Validations for empty content

    if not doc or len(doc.strip()) < 5:
        return {
            "issues": [
                {
                    "id": "0",
                    "severity": "High",
                    "issue_description": "Content is empty.",
                    "recommendation": "Please fill in the required content.",
                }
            ],
            "is_compliant": False,
        }

    structured_llm = llm.with_structured_output(AuditResponse)

    system_msg = f"""You are a Strict Project Charter Auditor.

   

    Your Goal: Verify if the User Content satisfies the Instructions.

   

    SECTION TITLE: {state.get("section_title")}

   

    INSTRUCTIONS (THE RULES):

    {criteria}

   

    USER CONTENT (THE EVIDENCE):

    {doc}

   

    RULES FOR AUDIT:

    1. **Placeholders**: If you see text inside angle brackets like <Add Name> or <Date>, flag this IMMEDIATELY as a 'High' severity issue called "Unresolved Placeholder".

    2. **Evidence**: If the Instruction asks for a "Screenshot" or "Link", and the text does not contain it, mark it as 'High' severity.

    3. **Mandatory Values**: If the Instruction mandates specific roles (e.g. "Q-PAR", "EPQ"), check if they are explicitly written.

    4. **Strictness**: If the content is vague or conversational filler, flag it.

    """

    try:
        response = structured_llm.invoke(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content="Audit this section."),
            ]
        )

        issues_dict = (
            [i.model_dump() for i in response.issues] if response.issues else []
        )

        return {"issues": issues_dict, "is_compliant": response.is_compliant}

    except Exception as e:
        print(f"Auditor Error: {e}")

        return {"issues": [], "is_compliant": False}


def fixer_node(state: AgentState):
    """

    Rewrites the 'document_text' to resolve a specific 'target_issue'.

    """

    print(f"--- Fixing Issue in Section: {state.get('section_title')} ---")

    doc = state.get("document_text", "")

    issue = state.get("target_issue", {})

    if not issue:
        return {"document_text": doc}  # No issue provided, return original

    system_msg = """You are an expert Technical Editor for Project Charters.

    Your task is to REWRITE the user's content to fix a specific issue reported by the auditor.

   

    GUIDELINES:

    1. Keep all correct information from the original text.

    2. Only apply the specific fix requested.

    3. Remove any placeholders (e.g., <Add Name>) by replacing them with a generic but realistic example or the specific value requested in the recommendation.

    4. Do not add conversational filler like "Here is the fixed text". Output ONLY the new content.

    """

    user_prompt = f"""

    ORIGINAL CONTENT:

    {doc}

   

    ISSUE TO FIX:

    {issue.get("issue_description")}

   

    RECOMMENDATION FOR FIX:

    {issue.get("recommendation")}

   

    Please rewrite the content to resolve this issue.

    """

    try:
        # We don't strictly need structured output here, but it ensures clean extraction

        structured_llm = llm.with_structured_output(FixResponse)

        response = structured_llm.invoke(
            [SystemMessage(content=system_msg), HumanMessage(content=user_prompt)]
        )

        # Return the UPDATED document text.

        # We also clear the target_issue so the state is clean.

        return {"document_text": response.fixed_content, "target_issue": None}

    except Exception as e:
        print(f"Fixer Error: {e}")

        return {"document_text": doc}  # Fail safe: return original


# --- 4. Routing Logic ---


def route_request(state: AgentState):
    """

    Decides whether to run the 'fixer' or the 'auditor'.

    If 'target_issue' is present in the state, it means the user clicked 'Auto-Fix'.

    Otherwise, it's a standard Audit check.

    """

    if state.get("target_issue"):
        return "fixer"

    return "auditor"


# --- 5. Graph Assembly ---

workflow = StateGraph(AgentState)


workflow.add_node("auditor", auditor_node)

workflow.add_node("fixer", fixer_node)


# Conditional Entry Point

# Checks state at the beginning to decide where to go

workflow.set_conditional_entry_point(
    route_request, {"auditor": "auditor", "fixer": "fixer"}
)


# Edges

workflow.add_edge("auditor", END)

workflow.add_edge(
    "fixer", END
)  # After fixing, we stop. User can re-audit manually if they want.


memory = MemorySaver()

graph = workflow.compile(checkpointer=memory)
