import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Import the strict Models and Prompts we just created
from backend.models import AgentState, AuditResponse, FixResponse
from backend.prompts import AUDITOR_SYSTEM_PROMPT, FIXER_SYSTEM_PROMPT

load_dotenv()

# --- 1. LLM Setup ---
# We use temperature=0 for maximum determinism (critical for compliance checking)
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
    temperature=0,
)

# --- 2. Node Definitions ---


def auditor_node(state: AgentState):
    """
    Analyzes the 'user_content' against 'criteria' and 'template_structure'.
    Determines if issues are fixable or require user input.
    """
    print(f"--- 🔍 Auditing Section: {state.get('section_title')} ---")

    # Extract inputs from state
    title = state.get("section_title", "Unknown Section")
    criteria = state.get("criteria", "")
    template_struct = state.get("template_structure", "")
    content = state.get("user_content", "")

    # 1. FAIL-FAST: Empty Content Check
    if not content or len(content.strip()) < 2:
        return {
            "issues": [
                {
                    "id": "0",
                    "severity": "High",
                    "issue_description": "Content is empty.",
                    "recommendation": "Please fill in the section using the template provided.",
                    "fixable": False,  # AI cannot fix empty air
                }
            ],
            "is_compliant": False,
        }

    # 2. Prepare the Prompt
    # We inject the specific context into the template we defined in prompts.py
    system_msg = AUDITOR_SYSTEM_PROMPT.format(
        section_title=title,
        criteria=criteria,
        template_structure=template_struct,
        user_content=content,
    )

    # 3. Call LLM with Structured Output (Pydantic)
    try:
        structured_llm = llm.with_structured_output(AuditResponse)
        response = structured_llm.invoke(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content="Perform the audit now."),
            ]
        )

        # Convert Pydantic models to dicts for JSON serialization in state
        issues_dict = (
            [i.model_dump() for i in response.issues] if response.issues else []
        )

        return {"issues": issues_dict, "is_compliant": response.is_compliant}

    except Exception as e:
        print(f"❌ Auditor Error: {e}")
        # Fallback error to prevent crash
        return {
            "issues": [
                {
                    "id": "err",
                    "severity": "High",
                    "issue_description": "AI Audit Service Failed.",
                    "recommendation": "Please try again.",
                    "fixable": False,
                }
            ],
            "is_compliant": False,
        }


def fixer_node(state: AgentState):
    """
    Rewrites the 'user_content' to solve a specific 'target_issue'.
    Enforces the 'template_structure'.
    """
    print(f"--- 🛠️ Fixing Issue in: {state.get('section_title')} ---")

    # Extract inputs
    template_struct = state.get("template_structure", "")
    content = state.get("user_content", "")
    issue = state.get("target_issue", {})

    # Safety Check: If no issue was selected, do nothing
    if not issue:
        return {"user_content": content}

    # 1. Prepare the Prompt
    system_msg = FIXER_SYSTEM_PROMPT.format(
        template_structure=template_struct,
        user_content=content,
        issue_description=issue.get("issue_description", "General Fix"),
        recommendation=issue.get("recommendation", "Follow template"),
    )

    # 2. Call LLM
    try:
        structured_llm = llm.with_structured_output(FixResponse)
        response = structured_llm.invoke(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content="Apply the fix."),
            ]
        )

        # Return UPDATED content
        # Crucial: We clear 'target_issue' to reset the trigger
        return {"user_content": response.fixed_content, "target_issue": None}

    except Exception as e:
        print(f"❌ Fixer Error: {e}")
        return {"user_content": content}  # Return original on failure
