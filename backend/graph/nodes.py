import streamlit as st
from langchain_core.messages import SystemMessage, HumanMessage

# Import the strict Models and Prompts
from backend.models import AgentState, AuditResponse, FixResponse
from backend.prompts import AUDITOR_SYSTEM_PROMPT, FIXER_SYSTEM_PROMPT
from backend.llm_factory import get_user_llm  # <--- Import Factory

# --- Node Definitions ---


def auditor_node(state: AgentState):
    print(f"--- 🔍 Auditing Section: {state.get('section_title')} ---")

    # 1. CHECK CREDENTIALS
    llm = get_user_llm()
    if not llm:
        return {
            "issues": [
                {
                    "id": "auth_err",
                    "severity": "High",
                    "issue_description": "LLM Credentials Missing",
                    "recommendation": "Please enter your API Key, Base URL, and Deployment Name in the Sidebar.",
                    "fixable": False,
                }
            ],
            "is_compliant": False,
        }

    # Extract inputs
    title = state.get("section_title", "Unknown Section")
    criteria = state.get("criteria", "")
    template_struct = state.get("template_structure", "")
    content = state.get("user_content", "")

    # 2. FAIL-FAST: Empty Content
    if not content or len(content.strip()) < 2:
        return {
            "issues": [
                {
                    "id": "0",
                    "severity": "High",
                    "issue_description": "Content is empty.",
                    "recommendation": "Please fill in the section using the template provided.",
                    "fixable": False,
                }
            ],
            "is_compliant": False,
        }

    # 3. CALL LLM
    system_msg = AUDITOR_SYSTEM_PROMPT.format(
        section_title=title,
        criteria=criteria,
        template_structure=template_struct,
        user_content=content,
    )

    try:
        structured_llm = llm.with_structured_output(AuditResponse)
        response = structured_llm.invoke(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content="Perform the audit now."),
            ]
        )
        issues_dict = (
            [i.model_dump() for i in response.issues] if response.issues else []
        )
        return {"issues": issues_dict, "is_compliant": response.is_compliant}

    except Exception as e:
        return {
            "issues": [
                {
                    "id": "err",
                    "severity": "High",
                    "issue_description": f"AI Error: {str(e)}",
                    "recommendation": "Check your LLM settings in the sidebar.",
                    "fixable": False,
                }
            ],
            "is_compliant": False,
        }


def fixer_node(state: AgentState):
    print(f"--- 🛠️ Fixing Issue in: {state.get('section_title')} ---")

    # 1. CHECK CREDENTIALS
    llm = get_user_llm()
    content = state.get("user_content", "")

    if not llm:
        st.error("Missing LLM Credentials! Please check the sidebar.")
        return {"user_content": content}

    # Extract inputs
    template_struct = state.get("template_structure", "")
    issue = state.get("target_issue", {})

    if not issue:
        return {"user_content": content}

    # 2. CALL LLM
    system_msg = FIXER_SYSTEM_PROMPT.format(
        template_structure=template_struct,
        user_content=content,
        issue_description=issue.get("issue_description", "General Fix"),
        recommendation=issue.get("recommendation", "Follow template"),
    )

    try:
        structured_llm = llm.with_structured_output(FixResponse)
        response = structured_llm.invoke(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content="Apply the fix."),
            ]
        )
        return {"user_content": response.fixed_content, "target_issue": None}

    except Exception as e:
        print(f"❌ Fixer Error: {e}")
        return {"user_content": content}
