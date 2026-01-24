# backend/ingestion.py
"""
PDF Import Pipeline.
Converts PDF files to structured sections using MarkItDown and LLM structuring.
"""

import tempfile
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from markitdown import MarkItDown


# --- Pydantic Models for LLM Structured Output ---


class ProjectSection(BaseModel):
    """Represents a single section extracted from a PDF."""

    title: str = Field(..., description="The section title (e.g., 'Problem Statement')")
    guidance: str = Field(
        ...,
        description="Guidance or instructions for this section. If not in PDF, infer standard PMBOK guidance.",
    )
    required_format: str = Field(
        ...,
        description="The format template (e.g., '[Problem] affects [Who]...'). Infer from text structure.",
    )
    content: str = Field(
        ..., description="The actual content extracted from the PDF for this section."
    )


class CharterStructure(BaseModel):
    """Wrapper for the list of sections extracted from a PDF."""

    sections: List[ProjectSection]


# --- PDF Statistics ---


def get_pdf_stats(raw_text: str, sections: List[ProjectSection]) -> dict:
    """
    Calculate statistics about the imported PDF.
    """
    word_count = len(raw_text.split())
    section_count = len(sections)
    # Estimate reading time (avg 200 wpm)
    reading_time = round(word_count / 200, 1)

    return {
        "word_count": word_count,
        "section_count": section_count,
        "reading_time_mins": reading_time,
    }


# --- Main Ingestion Logic ---


def parse_charter_pdf(
    uploaded_file,
    api_key: str,
    model_name: str = "gpt-4o",
    base_url: Optional[str] = None,
) -> List[ProjectSection]:
    """
    Parses a PDF file and extracts structured sections.

    1. Saves uploaded file stream to a temp file.
    2. Uses MarkItDown to convert PDF to Markdown text.
    3. Uses LLM with structured output to extract sections.

    Args:
        uploaded_file: Streamlit UploadedFile object (BytesIO-like)
        api_key: OpenAI API key
        model_name: Model to use for structuring
        base_url: Optional custom base URL for OpenAI API

    Returns:
        List of ProjectSection objects
    """

    # --- A. Convert PDF to Markdown ---
    md = MarkItDown()

    # Streamlit UploadedFile is a BytesIO, MarkItDown needs a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        result = md.convert(tmp_path)
        raw_text = result.text_content
    finally:
        os.remove(tmp_path)

    # --- B. Structuring with LLM ---
    llm_kwargs = {"api_key": api_key, "model": model_name, "temperature": 0}
    if base_url and base_url.strip():
        llm_kwargs["base_url"] = base_url

    llm = ChatOpenAI(**llm_kwargs).with_structured_output(CharterStructure)

    prompt = f"""You are an expert Project Manager AI.
Analyze the following Project Charter text converted from a PDF.

Your goal is to split this text into logical sections.
For each section, you must extract:
1. The Title.
2. The Content (the actual text from the document).
3. Guidance (Explain what this section is for. If not explicit, generate standard PM guidance based on the content).
4. Required Format (Create a template structure based on how the content is written).

RAW TEXT:
{raw_text[:50000]}
"""

    structured_data = llm.invoke(prompt)

    return structured_data.sections
