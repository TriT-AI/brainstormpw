
import pytest
from app.state_manager import load_template_into_state, get_sections, SESSION_KEY

class TestExampleErrors:
    """
    Functional tests to verify the Example Template loads with specific intentional errors.
    """

    @pytest.mark.functional
    def test_reviewers_has_missing_info_placeholder(self, mock_streamlit):
        """Verify Reviewers section contains the placeholder '<Add Name>'."""
        load_template_into_state("Example PMBOK Project Charter")
        sections = get_sections()
        
        # Section 0 is Reviewers
        reviewers_content = sections[0]["user_data"]["content"]
        assert "<Add Name of Department Head>" in reviewers_content
        assert "Sarah Connor" not in reviewers_content

    @pytest.mark.functional
    def test_objectives_has_contradiction(self, mock_streamlit):
        """Verify Objectives section contains the contradictory goal."""
        load_template_into_state("Example PMBOK Project Charter")
        sections = get_sections()
        
        # Section 2 is Objectives
        objectives_content = sections[2]["user_data"]["content"]
        assert "Increase average handling time" in objectives_content
        assert "Reduce Average Response Time" not in objectives_content

    @pytest.mark.functional
    def test_risks_has_formatting_error(self, mock_streamlit):
        """Verify Risks section is missing the 'Risk 1:' prefix."""
        load_template_into_state("Example PMBOK Project Charter")
        sections = get_sections()
        
        # Section 3 is Risks
        risks_content = sections[3]["user_data"]["content"]
        assert "Risk 1:" not in risks_content
        assert "hallucinate incorrect answers" in risks_content
