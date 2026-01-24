# tests/unit/test_ingestion.py
"""
Unit tests for the PDF ingestion module.
Tests Pydantic models and utility functions without requiring LLM calls.
"""

import pytest
from backend.ingestion import ProjectSection, CharterStructure, get_pdf_stats


class TestProjectSectionModel:
    """Tests for the ProjectSection Pydantic model."""

    def test_valid_section_creation(self):
        """Test creating a valid ProjectSection."""
        section = ProjectSection(
            title="Problem Statement",
            guidance="Define the core problem the project addresses.",
            required_format="[Problem] affects [Who] resulting in [Impact].",
            content="High customer churn affects the sales team resulting in 20% revenue loss.",
        )
        assert section.title == "Problem Statement"
        assert section.guidance == "Define the core problem the project addresses."
        assert section.required_format == "[Problem] affects [Who] resulting in [Impact]."
        assert "High customer churn" in section.content

    def test_section_model_dump(self):
        """Test that model_dump produces expected dictionary structure."""
        section = ProjectSection(
            title="Objectives",
            guidance="List SMART objectives.",
            required_format="Objective 1: ...",
            content="Reduce churn by 15% in Q2.",
        )
        data = section.model_dump()
        assert "title" in data
        assert "guidance" in data
        assert "required_format" in data
        assert "content" in data

    def test_section_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(Exception):
            ProjectSection(
                title="Incomplete",
                guidance="Some guidance",
                # missing required_format and content
            )


class TestCharterStructureModel:
    """Tests for the CharterStructure wrapper model."""

    def test_valid_charter_structure(self):
        """Test creating a valid CharterStructure with sections."""
        sections = [
            ProjectSection(
                title="Overview",
                guidance="Provide project overview.",
                required_format="The project is...",
                content="This project automates data entry.",
            ),
            ProjectSection(
                title="Goals",
                guidance="Define project goals.",
                required_format="Goal 1: ...",
                content="Goal 1: Reduce manual work by 50%.",
            ),
        ]
        charter = CharterStructure(sections=sections)
        assert len(charter.sections) == 2
        assert charter.sections[0].title == "Overview"
        assert charter.sections[1].title == "Goals"

    def test_charter_empty_sections(self):
        """Test that empty sections list is valid."""
        charter = CharterStructure(sections=[])
        assert charter.sections == []

    def test_charter_model_dump(self):
        """Test that model_dump produces expected structure."""
        section = ProjectSection(
            title="Test",
            guidance="Test guidance",
            required_format="Test format",
            content="Test content",
        )
        charter = CharterStructure(sections=[section])
        data = charter.model_dump()
        assert "sections" in data
        assert len(data["sections"]) == 1
        assert data["sections"][0]["title"] == "Test"


class TestGetPdfStats:
    """Tests for the get_pdf_stats utility function."""

    def test_basic_stats_calculation(self):
        """Test basic word count and section count."""
        raw_text = "This is a sample document with exactly nine words."
        sections = [
            ProjectSection(
                title="Section 1",
                guidance="g1",
                required_format="f1",
                content="c1",
            ),
            ProjectSection(
                title="Section 2",
                guidance="g2",
                required_format="f2",
                content="c2",
            ),
        ]
        stats = get_pdf_stats(raw_text, sections)
        assert stats["word_count"] == 9
        assert stats["section_count"] == 2
        assert stats["reading_time_mins"] == 0.0  # 9 / 200 = 0.045, rounds to 0.0

    def test_empty_text_stats(self):
        """Test stats for empty text."""
        stats = get_pdf_stats("", [])
        assert stats["word_count"] == 0
        assert stats["section_count"] == 0
        assert stats["reading_time_mins"] == 0.0

    def test_large_document_stats(self):
        """Test stats for larger text."""
        # Create a 1000 word document
        raw_text = " ".join(["word"] * 1000)
        sections = [
            ProjectSection(
                title=f"Section {i}",
                guidance="g",
                required_format="f",
                content="c",
            )
            for i in range(5)
        ]
        stats = get_pdf_stats(raw_text, sections)
        assert stats["word_count"] == 1000
        assert stats["section_count"] == 5
        assert stats["reading_time_mins"] == 5.0  # 1000 / 200 = 5.0
