
import pytest
from unittest.mock import MagicMock, patch
from app.state_manager import (
    update_section_audit_result, 
    update_global_audit_result, 
    get_section_by_id,
    get_global_audit_result,
    load_template_into_state,
    get_sections
)

class TestAILogicHandling:
    """
    Functional tests to verify how the application state handles
    results from the AI nodes (Auditor, Fixer, Consistency).
    We are NOT testing the LLM itself, but the STATE updates based on mock results.
    """

    @pytest.mark.functional
    def test_handle_illogical_content_audit(self, mock_streamlit):
        """Test that an audit result indicating logic issues flags the section."""
        # 1. Setup
        load_template_into_state("Standard Project Charter")
        sections = get_sections()
        target_section = sections[0]
        sec_id = target_section["id"]

        # 2. Mock Audit Result (Illogical)
        mock_audit_result = {
            "is_compliant": False,
            "issues": [
                {
                    "id": "logic_err_1",
                    "severity": "High",
                    "issue_description": "The timeline contradicts the scope.",
                    "recommendation": "Adjust timeline.",
                    "fixable": False
                }
            ]
        }

        # 3. Action
        update_section_audit_result(sec_id, mock_audit_result)

        # 4. Assertion
        updated_section = get_section_by_id(sec_id)
        assert updated_section["user_data"]["status"] == "flagged"
        assert updated_section["user_data"]["last_audit"]["is_compliant"] is False
        assert updated_section["user_data"]["last_audit"]["issues"][0]["id"] == "logic_err_1"

    @pytest.mark.functional
    def test_handle_format_error_audit(self, mock_streamlit):
        """Test that format errors flag the section."""
        # 1. Setup
        load_template_into_state("Standard Project Charter")
        sec_id = get_sections()[0]["id"]

        # 2. Mock Audit Result (Format Error)
        mock_audit_result = {
            "is_compliant": False,
            "issues": [
                {
                    "id": "fmt_1",
                    "severity": "Low",
                    "issue_description": "Missing 'Reviewers:' prefix.",
                    "recommendation": "Add prefix.",
                    "fixable": True
                }
            ]
        }

        # 3. Action
        update_section_audit_result(sec_id, mock_audit_result)

        # 4. Assertion
        updated_section = get_section_by_id(sec_id)
        assert updated_section["user_data"]["status"] == "flagged"
        # Ensure we capture that it is fixable
        assert updated_section["user_data"]["last_audit"]["issues"][0]["fixable"] is True

    @pytest.mark.functional
    def test_handle_auto_revision(self, mock_streamlit):
        """
        Test that applying a 'fix' updates the content only.
        NOTE: The explicit 'fixer_node' updates state directly, but typically
        the UI or a callback handles the update. We'll test the state update function usually used.
        In this app, `update_section_content` is used for manual edits, 
        but let's simulate the flow where the fixer returns new text.
        """
        from app.state_manager import update_section_content
        
        # 1. Setup
        load_template_into_state("Standard Project Charter")
        sec_id = get_sections()[0]["id"]
        
        # 2. Mock Fixer Output
        original_content = "Bad content"
        file_fixed_content = "Good content"
        
        # 3. Action (Apply Fix)
        # In the app, verify that updating content resets the audit status (as verified in existing tests)
        update_section_content(sec_id, file_fixed_content)
        
        # 4. Assertion
        updated_section = get_section_by_id(sec_id)
        assert updated_section["user_data"]["content"] == file_fixed_content
        assert updated_section["user_data"]["status"] == "draft" # Should reset to draft until re-audited

    @pytest.mark.functional
    def test_handle_global_consistency_result(self, mock_streamlit):
        """Test that global consistency results are stored correctly."""
        from app.state_manager import initialize_session
        
        # 0. Initialize Session
        initialize_session()

        # 1. Mock Global Result
        mock_global_result = {
            "is_consistent": False,
            "global_issues": [
                {
                    "id": "G-1",
                    "title": "Goal Conflict",
                    "description": "Risk section mentions ignoring cost...",
                    "related_sections": ["Objectives", "Risks"]
                }
            ]
        }

        # 2. Action
        update_global_audit_result(mock_global_result)

        # 3. Assertion
        stored_result = get_global_audit_result()
        assert stored_result["is_consistent"] is False
        assert len(stored_result["global_issues"]) == 1
        assert stored_result["global_issues"][0]["title"] == "Goal Conflict"
