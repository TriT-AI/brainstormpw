# tests/integration/test_ingestion_state.py
"""
Integration tests for the PDF ingestion pipeline and state management.
Tests the full flow from parsed sections to session state.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import io

from backend.ingestion import (
    ProjectSection,
    CharterStructure,
    parse_charter_pdf,
    get_pdf_stats,
)
from app.state_manager import load_imported_sections_into_state, SESSION_KEY


class TestLoadImportedSectionsIntoState:
    """Tests for load_imported_sections_into_state function."""

    def test_converts_sections_to_state_format(self, mock_streamlit):
        """Test that ProjectSection objects are correctly converted to state format."""
        sections = [
            ProjectSection(
                title="Problem Statement",
                guidance="Define the core problem",
                required_format="[Problem] affects [Who]",
                content="High churn affects sales team",
            ),
            ProjectSection(
                title="Objectives",
                guidance="List SMART objectives",
                required_format="Objective 1: ...",
                content="Reduce churn by 15%",
            ),
        ]

        load_imported_sections_into_state(sections)

        state = mock_streamlit["session_state"][SESSION_KEY]
        assert state["active_template_name"] == "Imported PDF"
        assert len(state["sections"]) == 2
        assert state["global_result"] is None

    def test_section_has_required_structure(self, mock_streamlit):
        """Test that each section has the correct nested structure."""
        sections = [
            ProjectSection(
                title="Test Section",
                guidance="Test guidance",
                required_format="Test format",
                content="Test content",
            )
        ]

        load_imported_sections_into_state(sections)

        section = mock_streamlit["session_state"][SESSION_KEY]["sections"][0]

        # Check top-level keys
        assert "id" in section
        assert "meta" in section
        assert "user_data" in section

        # Check meta structure
        assert section["meta"]["title"] == "Test Section"
        assert section["meta"]["criteria"] == "Test guidance"  # guidance -> criteria
        assert section["meta"]["template_structure"] == "Test format"  # required_format -> template_structure

        # Check user_data structure
        assert section["user_data"]["content"] == "Test content"
        assert section["user_data"]["last_audit"] is None
        assert section["user_data"]["status"] == "draft"

    def test_generates_unique_ids(self, mock_streamlit):
        """Test that each section gets a unique UUID."""
        sections = [
            ProjectSection(
                title=f"Section {i}",
                guidance="g",
                required_format="f",
                content="c",
            )
            for i in range(3)
        ]

        load_imported_sections_into_state(sections)

        ids = [s["id"] for s in mock_streamlit["session_state"][SESSION_KEY]["sections"]]
        assert len(ids) == 3
        assert len(set(ids)) == 3  # All unique

    def test_empty_sections_list(self, mock_streamlit):
        """Test handling of empty sections list."""
        load_imported_sections_into_state([])

        state = mock_streamlit["session_state"][SESSION_KEY]
        assert state["active_template_name"] == "Imported PDF"
        assert state["sections"] == []

    def test_overwrites_existing_state(self, mock_streamlit):
        """Test that importing overwrites any existing workspace."""
        # Set up existing state
        mock_streamlit["session_state"][SESSION_KEY] = {
            "active_template_name": "Old Template",
            "sections": [{"id": "old-section"}],
            "global_result": {"old": "result"},
        }

        sections = [
            ProjectSection(
                title="New Section",
                guidance="g",
                required_format="f",
                content="c",
            )
        ]

        load_imported_sections_into_state(sections)

        state = mock_streamlit["session_state"][SESSION_KEY]
        assert state["active_template_name"] == "Imported PDF"
        assert len(state["sections"]) == 1
        assert state["sections"][0]["meta"]["title"] == "New Section"
        assert state["global_result"] is None


class TestParseCharterPdf:
    """Tests for parse_charter_pdf function with mocked dependencies."""

    def test_converts_pdf_and_calls_llm(self):
        """Test the full pipeline with mocked MarkItDown and LLM."""
        # Mock UploadedFile
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"%PDF-1.4 fake pdf content"

        # Mock MarkItDown
        mock_md_result = MagicMock()
        mock_md_result.text_content = "# Project Charter\n\nThis is the converted text."

        mock_markitdown = MagicMock()
        mock_markitdown.convert.return_value = mock_md_result

        # Mock LLM response
        mock_sections = [
            ProjectSection(
                title="Overview",
                guidance="Project overview section",
                required_format="The project is...",
                content="This is the converted text.",
            )
        ]
        mock_charter = CharterStructure(sections=mock_sections)

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_charter
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("backend.ingestion.MarkItDown", return_value=mock_markitdown):
            with patch("backend.ingestion.ChatOpenAI", return_value=mock_llm):
                with patch("tempfile.NamedTemporaryFile", mock_open()):
                    with patch("os.remove"):
                        result = parse_charter_pdf(
                            mock_file, api_key="test-key", model_name="gpt-4o"
                        )

        assert len(result) == 1
        assert result[0].title == "Overview"

    def test_passes_api_credentials(self):
        """Test that API credentials are passed correctly to ChatOpenAI."""
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"%PDF-1.4"

        mock_md_result = MagicMock()
        mock_md_result.text_content = "Test content"
        mock_markitdown = MagicMock()
        mock_markitdown.convert.return_value = mock_md_result

        mock_charter = CharterStructure(sections=[])
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_charter
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("backend.ingestion.MarkItDown", return_value=mock_markitdown):
            with patch("backend.ingestion.ChatOpenAI") as mock_chat:
                mock_chat.return_value = mock_llm
                with patch("tempfile.NamedTemporaryFile", mock_open()):
                    with patch("os.remove"):
                        parse_charter_pdf(
                            mock_file,
                            api_key="my-api-key",
                            model_name="gpt-4-turbo",
                            base_url="https://custom.api.com",
                        )

                # Verify ChatOpenAI was called with correct args
                mock_chat.assert_called_once()
                call_kwargs = mock_chat.call_args[1]
                assert call_kwargs["api_key"] == "my-api-key"
                assert call_kwargs["model"] == "gpt-4-turbo"
                assert call_kwargs["base_url"] == "https://custom.api.com"
                assert call_kwargs["temperature"] == 0

    def test_handles_empty_base_url(self):
        """Test that empty base_url is not passed to ChatOpenAI."""
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"%PDF-1.4"

        mock_md_result = MagicMock()
        mock_md_result.text_content = "Test"
        mock_markitdown = MagicMock()
        mock_markitdown.convert.return_value = mock_md_result

        mock_charter = CharterStructure(sections=[])
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_charter
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("backend.ingestion.MarkItDown", return_value=mock_markitdown):
            with patch("backend.ingestion.ChatOpenAI") as mock_chat:
                mock_chat.return_value = mock_llm
                with patch("tempfile.NamedTemporaryFile", mock_open()):
                    with patch("os.remove"):
                        # Empty string base_url
                        parse_charter_pdf(mock_file, api_key="key", base_url="")

                call_kwargs = mock_chat.call_args[1]
                assert "base_url" not in call_kwargs

    def test_cleans_up_temp_file(self):
        """Test that temporary file is cleaned up after processing."""
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"%PDF-1.4"

        mock_md_result = MagicMock()
        mock_md_result.text_content = "Test"
        mock_markitdown = MagicMock()
        mock_markitdown.convert.return_value = mock_md_result

        mock_charter = CharterStructure(sections=[])
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_charter
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("backend.ingestion.MarkItDown", return_value=mock_markitdown):
            with patch("backend.ingestion.ChatOpenAI", return_value=mock_llm):
                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    mock_temp_instance = MagicMock()
                    mock_temp_instance.__enter__ = MagicMock(return_value=mock_temp_instance)
                    mock_temp_instance.__exit__ = MagicMock(return_value=False)
                    mock_temp_instance.name = "/tmp/test.pdf"
                    mock_temp.return_value = mock_temp_instance
                    
                    with patch("os.remove") as mock_remove:
                        parse_charter_pdf(mock_file, api_key="key")
                        mock_remove.assert_called_once_with("/tmp/test.pdf")


class TestIntegrationFullFlow:
    """End-to-end integration tests for the full import flow."""

    def test_full_import_flow(self, mock_streamlit):
        """Test the complete flow from PDF to session state."""
        # Setup mocks
        mock_file = MagicMock()
        mock_file.getvalue.return_value = b"%PDF-1.4 content"

        mock_md_result = MagicMock()
        mock_md_result.text_content = "# Charter\n\n## Problem\nWe have a problem."

        mock_markitdown = MagicMock()
        mock_markitdown.convert.return_value = mock_md_result

        mock_sections = [
            ProjectSection(
                title="Problem Statement",
                guidance="Define the problem",
                required_format="[Problem] affects [Who]",
                content="We have a problem.",
            ),
            ProjectSection(
                title="Solution",
                guidance="Describe the solution",
                required_format="The solution is...",
                content="We will solve it.",
            ),
        ]
        mock_charter = CharterStructure(sections=mock_sections)

        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_charter
        mock_llm.with_structured_output.return_value = mock_structured_llm

        with patch("backend.ingestion.MarkItDown", return_value=mock_markitdown):
            with patch("backend.ingestion.ChatOpenAI", return_value=mock_llm):
                with patch("tempfile.NamedTemporaryFile", mock_open()):
                    with patch("os.remove"):
                        # Step 1: Parse PDF
                        sections = parse_charter_pdf(mock_file, api_key="test-key")

                        # Step 2: Load into state
                        load_imported_sections_into_state(sections)

        # Verify final state
        state = mock_streamlit["session_state"][SESSION_KEY]
        assert state["active_template_name"] == "Imported PDF"
        assert len(state["sections"]) == 2

        # First section
        s1 = state["sections"][0]
        assert s1["meta"]["title"] == "Problem Statement"
        assert s1["meta"]["criteria"] == "Define the problem"
        assert s1["user_data"]["content"] == "We have a problem."
        assert s1["user_data"]["status"] == "draft"

        # Second section
        s2 = state["sections"][1]
        assert s2["meta"]["title"] == "Solution"


class TestGetPdfStatsIntegration:
    """Integration tests for PDF stats with real sections."""

    def test_stats_match_content(self):
        """Test that stats accurately reflect the content."""
        raw_text = "This is a comprehensive project charter document with multiple sections and detailed content. " * 10
        sections = [
            ProjectSection(
                title=f"Section {i}",
                guidance="guidance",
                required_format="format",
                content="content",
            )
            for i in range(5)
        ]

        stats = get_pdf_stats(raw_text, sections)

        # Should have 130 words (13 words * 10)
        assert stats["word_count"] == 130
        assert stats["section_count"] == 5
        assert stats["reading_time_mins"] == 0.7  # 130/200 = 0.65, rounds to 0.7
