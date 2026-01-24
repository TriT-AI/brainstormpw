"""
Unit tests for data/template_registry.py - Template registry and helper functions.
"""
import pytest
from data.template_registry import (
    TEMPLATES,
    SectionTemplate,
    get_available_templates,
    get_template_sections,
)


class TestTemplateRegistry:
    """Tests for the template registry constants and structure."""

    @pytest.mark.unit
    def test_templates_is_dict(self):
        """Test that TEMPLATES is a dictionary."""
        assert isinstance(TEMPLATES, dict)

    @pytest.mark.unit
    def test_templates_has_expected_keys(self):
        """Test that TEMPLATES contains expected template names."""
        template_names = list(TEMPLATES.keys())
        assert "Standard Project Charter" in template_names
        assert "Simple Document" in template_names

    @pytest.mark.unit
    def test_standard_project_charter_sections(self):
        """Test Standard Project Charter has expected sections."""
        sections = TEMPLATES["Standard Project Charter"]
        assert len(sections) == 4
        
        titles = [s["title"] for s in sections]
        assert "1. Reviewers" in titles
        assert "2. Problem Statement" in titles
        assert "3. Objectives (SMART)" in titles
        assert "4. Risks & Mitigation" in titles

    @pytest.mark.unit
    def test_simple_document_sections(self):
        """Test Simple Document has expected sections."""
        sections = TEMPLATES["Simple Document"]
        assert len(sections) == 2
        
        titles = [s["title"] for s in sections]
        assert "1. Executive Summary" in titles
        assert "2. Key Highlights" in titles

    @pytest.mark.unit
    def test_section_template_structure(self):
        """Test that each section has required keys."""
        for template_name, sections in TEMPLATES.items():
            for section in sections:
                assert "title" in section, f"Missing 'title' in {template_name}"
                assert "criteria" in section, f"Missing 'criteria' in {template_name}"
                assert "template_content" in section, f"Missing 'template_content' in {template_name}"

    @pytest.mark.unit
    def test_section_values_are_strings(self):
        """Test that section values are non-empty strings."""
        for template_name, sections in TEMPLATES.items():
            for section in sections:
                assert isinstance(section["title"], str) and section["title"]
                assert isinstance(section["criteria"], str) and section["criteria"]
                assert isinstance(section["template_content"], str) and section["template_content"]


class TestGetAvailableTemplates:
    """Tests for get_available_templates function."""

    @pytest.mark.unit
    def test_returns_list(self):
        """Test that function returns a list."""
        result = get_available_templates()
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_returns_all_template_names(self):
        """Test that function returns all template names."""
        result = get_available_templates()
        assert len(result) == len(TEMPLATES)
        for name in result:
            assert name in TEMPLATES

    @pytest.mark.unit
    def test_returns_string_names(self):
        """Test that all returned names are strings."""
        result = get_available_templates()
        for name in result:
            assert isinstance(name, str)

    @pytest.mark.unit
    def test_contains_expected_templates(self):
        """Test that expected templates are in the result."""
        result = get_available_templates()
        assert "Standard Project Charter" in result
        assert "Simple Document" in result


class TestGetTemplateSections:
    """Tests for get_template_sections function."""

    @pytest.mark.unit
    def test_returns_list_for_valid_template(self):
        """Test that function returns a list for valid template name."""
        result = get_template_sections("Standard Project Charter")
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_returns_correct_sections(self):
        """Test that function returns correct sections."""
        result = get_template_sections("Standard Project Charter")
        assert len(result) == 4
        assert result[0]["title"] == "1. Reviewers"

    @pytest.mark.unit
    def test_returns_empty_list_for_invalid_template(self):
        """Test that function returns empty list for non-existent template."""
        result = get_template_sections("Non-Existent Template")
        assert result == []

    @pytest.mark.unit
    def test_simple_document_sections(self):
        """Test getting Simple Document sections."""
        result = get_template_sections("Simple Document")
        assert len(result) == 2
        assert result[0]["title"] == "1. Executive Summary"

    @pytest.mark.unit
    def test_section_content_accessibility(self):
        """Test that section content is accessible."""
        result = get_template_sections("Standard Project Charter")
        first_section = result[0]
        
        assert "Reviewers" in first_section["title"]
        assert "Q-PAR" in first_section["criteria"]
        assert "<Add Name" in first_section["template_content"]

    @pytest.mark.unit
    def test_case_sensitivity(self):
        """Test that template name is case-sensitive."""
        result = get_template_sections("standard project charter")
        assert result == []  # Should not match due to case
