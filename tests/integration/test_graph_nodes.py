"""
Integration tests for backend/graph/nodes.py - Graph nodes with mocked LLM.
"""
import pytest
from unittest.mock import patch, MagicMock

from backend.models import AuditResponse, Issue, FixResponse, ConsistencyResponse, GlobalIssue


class TestAuditorNode:
    """Tests for the auditor_node function."""

    @pytest.mark.integration
    def test_returns_auth_error_without_credentials(self, mock_streamlit):
        """Test that auditor_node returns auth error when no LLM credentials."""
        from backend.graph.nodes import auditor_node
        
        state = {
            "section_title": "Test Section",
            "criteria": "Test criteria",
            "template_structure": "Test structure",
            "user_content": "Some content",
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=None):
            result = auditor_node(state)
        
        assert result["is_compliant"] is False
        assert len(result["issues"]) == 1
        assert result["issues"][0]["id"] == "auth_err"
        assert "Credentials Missing" in result["issues"][0]["issue_description"]

    @pytest.mark.integration
    def test_returns_empty_content_error(self, mock_streamlit):
        """Test that auditor_node returns error for empty content."""
        from backend.graph.nodes import auditor_node
        
        mock_llm = MagicMock()
        
        state = {
            "section_title": "Test Section",
            "criteria": "Test criteria",
            "template_structure": "Test structure",
            "user_content": "",  # Empty content
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = auditor_node(state)
        
        assert result["is_compliant"] is False
        assert len(result["issues"]) == 1
        assert result["issues"][0]["id"] == "0"
        assert "empty" in result["issues"][0]["issue_description"].lower()

    @pytest.mark.integration
    def test_returns_empty_content_error_for_whitespace(self, mock_streamlit):
        """Test that auditor_node treats whitespace-only content as empty."""
        from backend.graph.nodes import auditor_node
        
        mock_llm = MagicMock()
        
        state = {
            "section_title": "Test Section",
            "criteria": "Test criteria",
            "template_structure": "Test structure",
            "user_content": "  ",  # Whitespace only
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = auditor_node(state)
        
        assert result["is_compliant"] is False
        assert "empty" in result["issues"][0]["issue_description"].lower()

    @pytest.mark.integration
    def test_calls_llm_with_correct_prompt(self, mock_streamlit):
        """Test that auditor_node calls LLM with properly formatted prompt."""
        from backend.graph.nodes import auditor_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        # Create mock response
        mock_response = AuditResponse(is_compliant=True, issues=[])
        mock_structured_llm.invoke.return_value = mock_response
        
        state = {
            "section_title": "1. Reviewers",
            "criteria": "Must include Q-PAR",
            "template_structure": "Reviewers: <Name>",
            "user_content": "Reviewers: John Doe",
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = auditor_node(state)
        
        # Verify LLM was called with structured output
        mock_llm.with_structured_output.assert_called_once_with(AuditResponse)
        mock_structured_llm.invoke.assert_called_once()

    @pytest.mark.integration
    def test_returns_compliant_result(self, mock_streamlit):
        """Test that auditor_node returns compliant result from LLM."""
        from backend.graph.nodes import auditor_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        mock_response = AuditResponse(is_compliant=True, issues=[])
        mock_structured_llm.invoke.return_value = mock_response
        
        state = {
            "section_title": "Test",
            "criteria": "Test",
            "template_structure": "Test",
            "user_content": "Valid content here",
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = auditor_node(state)
        
        assert result["is_compliant"] is True
        assert result["issues"] == []

    @pytest.mark.integration
    def test_returns_issues_from_llm(self, mock_streamlit):
        """Test that auditor_node returns issues from LLM response."""
        from backend.graph.nodes import auditor_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        issue = Issue(
            id="1",
            severity="High",
            issue_description="Missing required field",
            recommendation="Add the field",
            fixable=False
        )
        mock_response = AuditResponse(is_compliant=False, issues=[issue])
        mock_structured_llm.invoke.return_value = mock_response
        
        state = {
            "section_title": "Test",
            "criteria": "Test",
            "template_structure": "Test",
            "user_content": "Incomplete content",
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = auditor_node(state)
        
        assert result["is_compliant"] is False
        assert len(result["issues"]) == 1
        assert result["issues"][0]["id"] == "1"

    @pytest.mark.integration
    def test_handles_llm_exception(self, mock_streamlit):
        """Test that auditor_node handles LLM exceptions gracefully."""
        from backend.graph.nodes import auditor_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.side_effect = Exception("LLM API Error")
        
        state = {
            "section_title": "Test",
            "criteria": "Test",
            "template_structure": "Test",
            "user_content": "Some content",
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = auditor_node(state)
        
        assert result["is_compliant"] is False
        assert result["issues"][0]["id"] == "err"
        assert "Error" in result["issues"][0]["issue_description"]


class TestFixerNode:
    """Tests for the fixer_node function."""

    @pytest.mark.integration
    def test_returns_original_content_without_credentials(self, mock_streamlit):
        """Test that fixer_node returns original content when no LLM credentials."""
        from backend.graph.nodes import fixer_node
        
        state = {
            "user_content": "Original content",
            "template_structure": "Template",
            "target_issue": {"id": "1", "issue_description": "Fix this"},
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=None):
            result = fixer_node(state)
        
        assert result["user_content"] == "Original content"

    @pytest.mark.integration
    def test_returns_original_content_without_target_issue(self, mock_streamlit):
        """Test that fixer_node returns original content when no target issue."""
        from backend.graph.nodes import fixer_node
        
        mock_llm = MagicMock()
        
        state = {
            "user_content": "Original content",
            "template_structure": "Template",
            "target_issue": None,
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = fixer_node(state)
        
        assert result["user_content"] == "Original content"

    @pytest.mark.integration
    def test_returns_fixed_content_from_llm(self, mock_streamlit):
        """Test that fixer_node returns fixed content from LLM."""
        from backend.graph.nodes import fixer_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        mock_response = FixResponse(fixed_content="Fixed content here")
        mock_structured_llm.invoke.return_value = mock_response
        
        state = {
            "section_title": "Test",
            "user_content": "Broken content",
            "template_structure": "Template",
            "target_issue": {"id": "1", "issue_description": "Fix this", "recommendation": "Do this"},
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = fixer_node(state)
        
        assert result["user_content"] == "Fixed content here"
        assert result["target_issue"] is None

    @pytest.mark.integration
    def test_handles_llm_exception(self, mock_streamlit):
        """Test that fixer_node handles LLM exceptions gracefully."""
        from backend.graph.nodes import fixer_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.side_effect = Exception("LLM Error")
        
        state = {
            "section_title": "Test",
            "user_content": "Original content",
            "template_structure": "Template",
            "target_issue": {"id": "1", "issue_description": "Fix"},
        }
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = fixer_node(state)
        
        assert result["user_content"] == "Original content"


class TestConsistencyNode:
    """Tests for the consistency_node function."""

    @pytest.mark.integration
    def test_returns_default_without_credentials(self, mock_streamlit):
        """Test that consistency_node returns default response without credentials."""
        from backend.graph.nodes import consistency_node
        
        with patch('backend.graph.nodes.get_user_llm', return_value=None):
            result = consistency_node("Full document content")
        
        assert result["is_consistent"] is False
        assert result["global_issues"] == []

    @pytest.mark.integration
    def test_returns_consistent_result(self, mock_streamlit):
        """Test that consistency_node returns consistent result from LLM."""
        from backend.graph.nodes import consistency_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        mock_response = ConsistencyResponse(is_consistent=True, global_issues=[])
        mock_structured_llm.invoke.return_value = mock_response
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = consistency_node("Consistent document content")
        
        assert result["is_consistent"] is True
        assert result["global_issues"] == []

    @pytest.mark.integration
    def test_returns_global_issues(self, mock_streamlit):
        """Test that consistency_node returns global issues from LLM."""
        from backend.graph.nodes import consistency_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        
        issue = GlobalIssue(
            id="G-1",
            title="Contradiction",
            description="Sections conflict",
            related_sections=["Section 1", "Section 2"]
        )
        mock_response = ConsistencyResponse(is_consistent=False, global_issues=[issue])
        mock_structured_llm.invoke.return_value = mock_response
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = consistency_node("Inconsistent document content")
        
        assert result["is_consistent"] is False
        assert len(result["global_issues"]) == 1
        assert result["global_issues"][0]["id"] == "G-1"

    @pytest.mark.integration
    def test_handles_llm_exception(self, mock_streamlit):
        """Test that consistency_node handles LLM exceptions gracefully."""
        from backend.graph.nodes import consistency_node
        
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.side_effect = Exception("LLM Error")
        
        with patch('backend.graph.nodes.get_user_llm', return_value=mock_llm):
            result = consistency_node("Document content")
        
        assert result["is_consistent"] is False
        assert result["global_issues"] == []
