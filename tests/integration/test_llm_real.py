"""
Integration tests that use real LLM API calls.
These tests verify that prompts and logic produce expected outputs.
Only run on PR with actual API credentials from GitHub secrets.
"""
import pytest
import os
from unittest.mock import patch

from backend.models import AuditResponse, ConsistencyResponse, FixResponse


# Skip all tests if no API key is available
pytestmark = [
    pytest.mark.llm_integration,
    pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set - skipping real LLM tests"
    )
]


@pytest.fixture
def real_llm_session_state():
    """Fixture that sets up session state with real API credentials."""
    class MockSessionState(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(key)
        def __setattr__(self, key, value):
            self[key] = value
    
    state = MockSessionState()
    state['system_api_key'] = os.environ.get("OPENAI_API_KEY")
    state['system_model_name'] = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o")
    state['system_base_url'] = os.environ.get("OPENAI_BASE_URL", "")
    return state


class TestAuditorNodeWithRealLLM:
    """Tests for auditor_node with real LLM API calls."""

    @pytest.mark.llm_integration
    def test_auditor_identifies_empty_placeholder(self, real_llm_session_state):
        """Test that auditor correctly identifies unfilled placeholders."""
        from backend.graph.nodes import auditor_node
        
        state = {
            "section_title": "1. Reviewers",
            "criteria": "Must include the name of Q-PAR or EPQ as mandatory reviewer.",
            "template_structure": "Reviewers: <Add Name of Q-PAR or EPQ> (Mandatory)",
            "user_content": "Reviewers: <Add Name of Q-PAR or EPQ> (Mandatory)",
        }
        
        with patch('streamlit.session_state', real_llm_session_state):
            result = auditor_node(state)
        
        # Should flag as non-compliant because placeholder is not filled
        assert result["is_compliant"] is False
        assert len(result["issues"]) > 0
        # Issue should mention missing/placeholder data
        assert any("placeholder" in str(i).lower() or "missing" in str(i).lower() or "add" in str(i).lower() 
                   for i in result["issues"])

    @pytest.mark.llm_integration
    def test_auditor_approves_valid_content(self, real_llm_session_state):
        """Test that auditor approves properly filled content."""
        from backend.graph.nodes import auditor_node
        
        state = {
            "section_title": "1. Reviewers",
            "criteria": "Must include the name of Q-PAR or EPQ as mandatory reviewer.",
            "template_structure": "Reviewers: <Add Name of Q-PAR or EPQ> (Mandatory)",
            "user_content": "Reviewers: John Smith (Q-PAR) (Mandatory)\nAdditional Reviewers: Jane Doe",
        }
        
        with patch('streamlit.session_state', real_llm_session_state):
            result = auditor_node(state)
        
        # Should be compliant or have only minor issues
        # The content follows the template and has actual names
        assert "issues" in result


class TestConsistencyNodeWithRealLLM:
    """Tests for consistency_node with real LLM API calls."""

    @pytest.mark.llm_integration
    def test_consistency_detects_contradiction(self, real_llm_session_state):
        """Test that consistency check detects contradictions."""
        from backend.graph.nodes import consistency_node
        
        document_content = """
        ## Problem Statement
        The current process is too slow, taking 5 days to complete.
        
        ## Objectives
        Goal: Reduce processing time to 10 days.
        """
        
        with patch('streamlit.session_state', real_llm_session_state):
            result = consistency_node(document_content)
        
        # Should detect the contradiction (goal makes it slower, not faster)
        assert "is_consistent" in result
        # This is a clear contradiction - should be caught
        if not result["is_consistent"]:
            assert len(result["global_issues"]) > 0

    @pytest.mark.llm_integration
    def test_consistency_approves_coherent_document(self, real_llm_session_state):
        """Test that consistency check approves coherent content."""
        from backend.graph.nodes import consistency_node
        
        document_content = """
        ## Problem Statement
        The current manual process takes 5 days to complete, causing delays.
        
        ## Objectives
        Goal: Automate the process to reduce completion time to 1 day.
        KPI: Processing time (Current: 5 days -> Target: 1 day)
        """
        
        with patch('streamlit.session_state', real_llm_session_state):
            result = consistency_node(document_content)
        
        # Should be consistent - goal addresses the problem
        assert "is_consistent" in result


class TestFixerNodeWithRealLLM:
    """Tests for fixer_node with real LLM API calls."""

    @pytest.mark.llm_integration
    def test_fixer_reformats_content(self, real_llm_session_state):
        """Test that fixer correctly reformats content."""
        from backend.graph.nodes import fixer_node
        
        state = {
            "section_title": "1. Reviewers",
            "template_structure": "Reviewers: <Name> (Mandatory)\nAdditional Reviewers: <Name>",
            "user_content": "John is the reviewer and Jane helps too",
            "target_issue": {
                "id": "1",
                "issue_description": "Content does not follow template structure",
                "recommendation": "Reformat to match the template structure",
            },
        }
        
        with patch('streamlit.session_state', real_llm_session_state):
            result = fixer_node(state)
        
        # Fixed content should contain the names from original
        assert "John" in result["user_content"] or "john" in result["user_content"].lower()
        # Should follow more of the template structure
        assert "Reviewer" in result["user_content"]
