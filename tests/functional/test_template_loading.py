"""
Functional tests for template loading workflows.
"""
import pytest
from unittest.mock import patch


class TestTemplateLoadingWorkflow:
    """Tests for the complete template loading workflow."""

    @pytest.mark.functional
    def test_complete_template_load_workflow(self, mock_streamlit):
        """Test the complete workflow of loading a template."""
        from app.state_manager import initialize_session, load_template_into_state, get_sections
        from data.template_registry import get_available_templates
        
        # Step 1: Initialize session
        initialize_session()
        assert get_sections() == []
        
        # Step 2: Get available templates
        templates = get_available_templates()
        assert len(templates) > 0
        
        # Step 3: Load a template
        load_template_into_state(templates[0])
        
        # Step 4: Verify sections are loaded
        sections = get_sections()
        assert len(sections) > 0
        
        # Step 5: Verify each section has proper structure
        for section in sections:
            assert section["user_data"]["status"] == "draft"
            assert section["meta"]["title"]
            assert section["meta"]["criteria"]

    @pytest.mark.functional
    def test_template_switching(self, mock_streamlit):
        """Test switching between templates."""
        from app.state_manager import initialize_session, load_template_into_state, get_sections, SESSION_KEY
        
        initialize_session()
        
        # Load first template
        load_template_into_state("Standard Project Charter")
        first_count = len(get_sections())
        first_template = mock_streamlit['session_state'][SESSION_KEY]["active_template_name"]
        
        # Load second template
        load_template_into_state("Simple Document")
        second_count = len(get_sections())
        second_template = mock_streamlit['session_state'][SESSION_KEY]["active_template_name"]
        
        # Verify switch happened
        assert first_template != second_template
        assert first_count != second_count
        assert second_template == "Simple Document"

    @pytest.mark.functional
    def test_section_editing_resets_audit(self, mock_streamlit):
        """Test that editing a section resets its audit state."""
        from app.state_manager import (
            load_template_into_state, 
            get_sections, 
            update_section_content,
            update_section_audit_result
        )
        
        load_template_into_state("Simple Document")
        section = get_sections()[0]
        section_id = section["id"]
        
        # Simulate audit completion
        update_section_audit_result(section_id, {"is_compliant": True, "issues": []})
        assert get_sections()[0]["user_data"]["status"] == "compliant"
        
        # Edit the section
        update_section_content(section_id, "New content")
        
        # Verify audit is reset
        updated_section = get_sections()[0]
        assert updated_section["user_data"]["status"] == "draft"
        assert updated_section["user_data"]["last_audit"] is None

    @pytest.mark.functional
    def test_multiple_section_audits(self, mock_streamlit):
        """Test auditing multiple sections independently."""
        from app.state_manager import (
            load_template_into_state, 
            get_sections, 
            update_section_audit_result
        )
        
        load_template_into_state("Standard Project Charter")
        sections = get_sections()
        
        # Audit first section as compliant
        update_section_audit_result(sections[0]["id"], {"is_compliant": True, "issues": []})
        
        # Audit second section as flagged
        update_section_audit_result(sections[1]["id"], {"is_compliant": False, "issues": [{"id": "1"}]})
        
        # Verify independent statuses
        updated_sections = get_sections()
        assert updated_sections[0]["user_data"]["status"] == "compliant"
        assert updated_sections[1]["user_data"]["status"] == "flagged"
        assert updated_sections[2]["user_data"]["status"] == "draft"

    @pytest.mark.functional
    def test_workspace_clear_and_reload(self, mock_streamlit):
        """Test clearing workspace and reloading template."""
        from app.state_manager import (
            load_template_into_state, 
            get_sections, 
            clear_workspace,
            update_section_content
        )
        
        load_template_into_state("Simple Document")
        section_id = get_sections()[0]["id"]
        update_section_content(section_id, "User input here")
        
        # Clear workspace
        clear_workspace()
        assert get_sections() == []
        
        # Reload template
        load_template_into_state("Simple Document")
        sections = get_sections()
        
        # Verify fresh start
        assert len(sections) == 2
        assert sections[0]["user_data"]["content"] == ""
