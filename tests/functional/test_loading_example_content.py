
import pytest
from app.state_manager import load_template_into_state, SESSION_KEY

class TestLoadExampleContent:
    """Functional tests for loading templates with example content."""

    @pytest.mark.functional
    def test_loads_example_content_correctly(self, mock_streamlit):
        """Test that loading the Example Charter populates user_data['content']."""
        
        load_template_into_state("Example PMBOK Project Charter")
        
        workspace = mock_streamlit['session_state'][SESSION_KEY]
        sections = workspace["sections"]
        
        assert len(sections) > 0
        
        # Check first section
        first_section = sections[0]
        assert first_section["user_data"]["content"] != ""
        assert "Jane Doe" in first_section["user_data"]["content"] # From our hardcoded example

    @pytest.mark.functional
    def test_loads_empty_content_for_standard_template(self, mock_streamlit):
        """Test that loading Standard Charter still results in empty content."""
        
        load_template_into_state("Standard Project Charter")
        
        workspace = mock_streamlit['session_state'][SESSION_KEY]
        sections = workspace["sections"]
        
        for section in sections:
            assert section["user_data"]["content"] == ""
