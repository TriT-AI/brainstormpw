"""
Functional tests for app/state_manager.py - State management workflows.
"""
import pytest
from unittest.mock import patch, MagicMock
import uuid


class TestInitializeSession:
    """Tests for initialize_session function."""

    @pytest.mark.functional
    def test_creates_session_key_if_not_exists(self, mock_streamlit):
        """Test that initialize_session creates the session key structure."""
        from app.state_manager import initialize_session, SESSION_KEY
        
        initialize_session()
        
        assert SESSION_KEY in mock_streamlit['session_state']
        workspace = mock_streamlit['session_state'][SESSION_KEY]
        assert workspace["active_template_name"] is None
        assert workspace["sections"] == []
        assert "global_result" in workspace

    @pytest.mark.functional
    def test_preserves_existing_session(self, mock_streamlit):
        """Test that initialize_session doesn't overwrite existing session."""
        from app.state_manager import initialize_session, SESSION_KEY
        
        # Pre-populate session
        mock_streamlit['session_state'][SESSION_KEY] = {
            "active_template_name": "Test Template",
            "sections": [{"id": "test"}],
            "global_result": {"test": True}
        }
        
        initialize_session()
        
        workspace = mock_streamlit['session_state'][SESSION_KEY]
        assert workspace["active_template_name"] == "Test Template"
        assert len(workspace["sections"]) == 1


class TestLoadTemplateIntoState:
    """Tests for load_template_into_state function."""

    @pytest.mark.functional
    def test_loads_standard_project_charter(self, mock_streamlit):
        """Test loading Standard Project Charter template."""
        from app.state_manager import load_template_into_state, SESSION_KEY
        
        load_template_into_state("Standard Project Charter")
        
        workspace = mock_streamlit['session_state'][SESSION_KEY]
        assert workspace["active_template_name"] == "Standard Project Charter"
        assert len(workspace["sections"]) == 4

    @pytest.mark.functional
    def test_section_has_correct_structure(self, mock_streamlit):
        """Test that loaded sections have correct structure."""
        from app.state_manager import load_template_into_state, SESSION_KEY
        
        load_template_into_state("Standard Project Charter")
        
        section = mock_streamlit['session_state'][SESSION_KEY]["sections"][0]
        assert "id" in section
        assert "meta" in section
        assert "user_data" in section
        
        assert "title" in section["meta"]
        assert "criteria" in section["meta"]
        assert "template_structure" in section["meta"]
        
        assert "content" in section["user_data"]
        assert "last_audit" in section["user_data"]
        assert "status" in section["user_data"]

    @pytest.mark.functional
    def test_section_starts_with_draft_status(self, mock_streamlit):
        """Test that loaded sections start with draft status."""
        from app.state_manager import load_template_into_state, SESSION_KEY
        
        load_template_into_state("Standard Project Charter")
        
        for section in mock_streamlit['session_state'][SESSION_KEY]["sections"]:
            assert section["user_data"]["status"] == "draft"
            assert section["user_data"]["content"] == ""
            assert section["user_data"]["last_audit"] is None

    @pytest.mark.functional
    def test_overwrites_existing_workspace(self, mock_streamlit):
        """Test that loading template overwrites existing workspace."""
        from app.state_manager import load_template_into_state, SESSION_KEY
        
        # First load
        load_template_into_state("Standard Project Charter")
        assert len(mock_streamlit['session_state'][SESSION_KEY]["sections"]) == 4
        
        # Second load with different template
        load_template_into_state("Simple Document")
        assert len(mock_streamlit['session_state'][SESSION_KEY]["sections"]) == 2
        assert mock_streamlit['session_state'][SESSION_KEY]["active_template_name"] == "Simple Document"

    @pytest.mark.functional
    def test_generates_unique_section_ids(self, mock_streamlit):
        """Test that each section gets a unique UUID."""
        from app.state_manager import load_template_into_state, SESSION_KEY
        
        load_template_into_state("Standard Project Charter")
        
        sections = mock_streamlit['session_state'][SESSION_KEY]["sections"]
        ids = [s["id"] for s in sections]
        assert len(ids) == len(set(ids))  # All unique


class TestGetSections:
    """Tests for get_sections function."""

    @pytest.mark.functional
    def test_returns_empty_list_initially(self, mock_streamlit):
        """Test that get_sections returns empty list before template load."""
        from app.state_manager import initialize_session, get_sections
        
        initialize_session()
        result = get_sections()
        
        assert result == []

    @pytest.mark.functional
    def test_returns_loaded_sections(self, mock_streamlit):
        """Test that get_sections returns sections after template load."""
        from app.state_manager import load_template_into_state, get_sections
        
        load_template_into_state("Simple Document")
        result = get_sections()
        
        assert len(result) == 2


class TestGetSectionById:
    """Tests for get_section_by_id function."""

    @pytest.mark.functional
    def test_returns_correct_section(self, mock_streamlit):
        """Test that get_section_by_id returns the correct section."""
        from app.state_manager import load_template_into_state, get_sections, get_section_by_id
        
        load_template_into_state("Standard Project Charter")
        sections = get_sections()
        target_id = sections[1]["id"]
        
        result = get_section_by_id(target_id)
        
        assert result is not None
        assert result["id"] == target_id

    @pytest.mark.functional
    def test_returns_none_for_invalid_id(self, mock_streamlit):
        """Test that get_section_by_id returns None for invalid ID."""
        from app.state_manager import load_template_into_state, get_section_by_id
        
        load_template_into_state("Standard Project Charter")
        result = get_section_by_id("non-existent-id")
        
        assert result is None


class TestUpdateSectionContent:
    """Tests for update_section_content function."""

    @pytest.mark.functional
    def test_updates_content(self, mock_streamlit):
        """Test that update_section_content updates the content."""
        from app.state_manager import load_template_into_state, get_sections, update_section_content
        
        load_template_into_state("Simple Document")
        section_id = get_sections()[0]["id"]
        
        update_section_content(section_id, "New content here")
        
        section = get_sections()[0]
        assert section["user_data"]["content"] == "New content here"

    @pytest.mark.functional
    def test_resets_status_on_edit(self, mock_streamlit):
        """Test that editing content resets status to draft."""
        from app.state_manager import (
            load_template_into_state, get_sections, 
            update_section_content, update_section_audit_result
        )
        
        load_template_into_state("Simple Document")
        section_id = get_sections()[0]["id"]
        
        # Set to compliant
        update_section_audit_result(section_id, {"is_compliant": True, "issues": []})
        assert get_sections()[0]["user_data"]["status"] == "compliant"
        
        # Edit content - should reset to draft
        update_section_content(section_id, "Updated content")
        assert get_sections()[0]["user_data"]["status"] == "draft"
        assert get_sections()[0]["user_data"]["last_audit"] is None


class TestUpdateSectionAuditResult:
    """Tests for update_section_audit_result function."""

    @pytest.mark.functional
    def test_sets_compliant_status(self, mock_streamlit):
        """Test that compliant audit result sets compliant status."""
        from app.state_manager import load_template_into_state, get_sections, update_section_audit_result
        
        load_template_into_state("Simple Document")
        section_id = get_sections()[0]["id"]
        
        update_section_audit_result(section_id, {"is_compliant": True, "issues": []})
        
        section = get_sections()[0]
        assert section["user_data"]["status"] == "compliant"
        assert section["user_data"]["last_audit"]["is_compliant"] is True

    @pytest.mark.functional
    def test_sets_flagged_status(self, mock_streamlit):
        """Test that non-compliant audit result sets flagged status."""
        from app.state_manager import load_template_into_state, get_sections, update_section_audit_result
        
        load_template_into_state("Simple Document")
        section_id = get_sections()[0]["id"]
        
        update_section_audit_result(section_id, {"is_compliant": False, "issues": [{"id": "1"}]})
        
        section = get_sections()[0]
        assert section["user_data"]["status"] == "flagged"


class TestGlobalAuditFunctions:
    """Tests for global audit result functions."""

    @pytest.mark.functional
    def test_update_and_get_global_audit_result(self, mock_streamlit):
        """Test updating and retrieving global audit result."""
        from app.state_manager import (
            initialize_session, 
            update_global_audit_result, 
            get_global_audit_result
        )
        
        initialize_session()
        
        global_result = {"is_consistent": True, "global_issues": []}
        update_global_audit_result(global_result)
        
        result = get_global_audit_result()
        assert result["is_consistent"] is True

    @pytest.mark.functional
    def test_get_global_audit_result_returns_none_initially(self, mock_streamlit):
        """Test that get_global_audit_result returns None initially."""
        from app.state_manager import initialize_session, get_global_audit_result
        
        initialize_session()
        result = get_global_audit_result()
        
        assert result is None


class TestClearWorkspace:
    """Tests for clear_workspace function."""

    @pytest.mark.functional
    def test_clears_workspace(self, mock_streamlit):
        """Test that clear_workspace resets the workspace."""
        from app.state_manager import load_template_into_state, clear_workspace, SESSION_KEY
        
        load_template_into_state("Standard Project Charter")
        assert len(mock_streamlit['session_state'][SESSION_KEY]["sections"]) == 4
        
        clear_workspace()
        
        workspace = mock_streamlit['session_state'][SESSION_KEY]
        assert workspace["active_template_name"] is None
        assert workspace["sections"] == []
