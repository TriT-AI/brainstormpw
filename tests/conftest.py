"""
Shared pytest fixtures for BrainstormPW tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any


# --- Mock Streamlit Session State ---

class MockSessionState(dict):
    """A dict-like object that mimics streamlit's session_state behavior."""
    
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'MockSessionState' has no attribute '{key}'")
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'MockSessionState' has no attribute '{key}'")


@pytest.fixture
def mock_session_state():
    """Provides a clean mock session state for each test."""
    return MockSessionState()


@pytest.fixture
def mock_streamlit(mock_session_state):
    """
    Patches streamlit module with mocked components.
    Use this fixture when testing code that imports streamlit.
    """
    with patch('streamlit.session_state', mock_session_state):
        with patch('streamlit.error') as mock_error:
            with patch('streamlit.warning') as mock_warning:
                with patch('streamlit.success') as mock_success:
                    yield {
                        'session_state': mock_session_state,
                        'error': mock_error,
                        'warning': mock_warning,
                        'success': mock_success,
                    }


# --- Sample Data Fixtures ---

@pytest.fixture
def sample_issue() -> Dict[str, Any]:
    """Returns a sample Issue dictionary."""
    return {
        "id": "1",
        "severity": "High",
        "issue_description": "Missing reviewer name",
        "recommendation": "Add the Q-PAR or EPQ name as mandatory reviewer",
        "fixable": False
    }


@pytest.fixture
def sample_audit_response() -> Dict[str, Any]:
    """Returns a sample AuditResponse dictionary."""
    return {
        "is_compliant": False,
        "issues": [
            {
                "id": "1",
                "severity": "High",
                "issue_description": "Content is missing required fields",
                "recommendation": "Fill in all required fields",
                "fixable": False
            }
        ]
    }


@pytest.fixture
def sample_global_issue() -> Dict[str, Any]:
    """Returns a sample GlobalIssue dictionary."""
    return {
        "id": "G-1",
        "title": "Goal contradicts Problem",
        "description": "The stated goal does not address the identified problem",
        "related_sections": ["2. Problem Statement", "3. Objectives (SMART)"]
    }


@pytest.fixture
def sample_section() -> Dict[str, Any]:
    """Returns a sample section dictionary as used in state manager."""
    return {
        "id": "test-uuid-123",
        "meta": {
            "title": "1. Reviewers",
            "criteria": "Must include Q-PAR or EPQ name",
            "template_structure": "Reviewers: <Add Name>"
        },
        "user_data": {
            "content": "",
            "last_audit": None,
            "status": "draft"
        }
    }


@pytest.fixture
def sample_agent_state() -> Dict[str, Any]:
    """Returns a sample AgentState dictionary."""
    return {
        "section_title": "1. Reviewers",
        "criteria": "Must include Q-PAR or EPQ name as mandatory reviewer",
        "template_structure": "Reviewers: <Add Name of Q-PAR or EPQ>",
        "user_content": "Reviewers: John Doe",
        "issues": [],
        "is_compliant": True,
        "target_issue": None
    }


# --- Mock LLM Fixtures ---

@pytest.fixture
def mock_llm():
    """Returns a mock LLM that can be configured for different responses."""
    llm = MagicMock()
    structured_llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm
    return llm, structured_llm


@pytest.fixture
def mock_llm_factory(mock_llm):
    """Patches get_user_llm to return the mock LLM."""
    llm, structured_llm = mock_llm
    with patch('backend.llm_factory.get_user_llm', return_value=llm):
        yield llm, structured_llm
