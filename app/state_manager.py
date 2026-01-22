import uuid
import streamlit as st
from typing import List, Dict, Optional
from data.template_registry import get_template_sections

# --- CONSTANTS ---
SESSION_KEY = "document_workspace"


def initialize_session():
    """Ensures the session state has the necessary structure on app load."""
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = {
            "active_template_name": None,
            "sections": [],  # List of section dictionaries
            "global_result": None,
        }


def load_template_into_state(template_name: str):
    """
    Loads a template from the registry into the session state.
    WARNING: This overwrites the current workspace.
    """
    raw_sections = get_template_sections(template_name)

    new_sections = []
    for section in raw_sections:
        new_sections.append(
            {
                "id": str(uuid.uuid4()),
                "meta": {
                    "title": section["title"],
                    "criteria": section["criteria"],
                    "template_structure": section["template_content"],
                },
                "user_data": {
                    "content": "",  # Start empty so user sees placeholder hint
                    "last_audit": None,  # Stores the full AuditResponse dict
                    "status": "draft",  # Options: 'draft', 'compliant', 'flagged'
                },
            }
        )

    st.session_state[SESSION_KEY] = {
        "active_template_name": template_name,
        "sections": new_sections,
    }


def get_sections() -> List[Dict]:
    """Retrieve all sections from the current session."""
    return st.session_state[SESSION_KEY].get("sections", [])


def get_section_by_id(section_id: str) -> Optional[Dict]:
    """Helper to find a specific section by its UUID."""
    sections = get_sections()
    for sec in sections:
        if sec["id"] == section_id:
            return sec
    return None


def update_section_content(section_id: str, new_content: str):
    """Updates the user content for a specific section."""
    section = get_section_by_id(section_id)
    if section:
        section["user_data"]["content"] = new_content
        # Reset status on edit because the previous audit is now stale
        if section["user_data"]["status"] != "draft":
            section["user_data"]["status"] = "draft"
            section["user_data"]["last_audit"] = None


def update_section_audit_result(section_id: str, audit_result: dict):
    """Updates the audit status based on the AI response."""
    section = get_section_by_id(section_id)
    if section:
        section["user_data"]["last_audit"] = audit_result
        section["user_data"]["status"] = (
            "compliant" if audit_result.get("is_compliant") else "flagged"
        )


def update_global_audit_result(global_result: dict):
    """Updates the session state with the whole-document Logic Check results."""
    st.session_state[SESSION_KEY]["global_result"] = global_result


def get_global_audit_result() -> Optional[Dict]:
    """Retrieves the global consistency check results."""
    return st.session_state[SESSION_KEY].get("global_result")


def clear_workspace():
    """Resets the workspace to empty."""
    st.session_state[SESSION_KEY] = {"active_template_name": None, "sections": []}
