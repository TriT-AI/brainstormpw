
import pytest
from data.template_registry import TEMPLATES, get_available_templates, get_template_sections

class TestExampleProjectCharter:
    """Tests specifically for the Example PMBOK Project Charter."""

    def test_example_charter_exists(self):
        """Verify the template is in the registry."""
        templates = get_available_templates()
        assert "Example PMBOK Project Charter" in templates

    def test_example_charter_has_example_content(self):
        """Verify that all sections in the example charter have content."""
        sections = get_template_sections("Example PMBOK Project Charter")
        assert len(sections) > 0
        for section in sections:
            assert "example_content" in section
            assert len(section["example_content"]) > 10  # Ensure it's not empty/trivial

    def test_standard_charter_has_no_example_content(self):
        """Verify we didn't accidentally add content to the standard template."""
        sections = get_template_sections("Standard Project Charter")
        for section in sections:
            # It's okay if the key exists but is None, or doesn't exist.
            # But based on our implementation, we didn't add the key at all.
            assert "example_content" not in section
