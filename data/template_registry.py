from typing import List, Dict, TypedDict


# --- 1. Type Definitions (For better code intelligence) ---
class SectionTemplate(TypedDict):
    title: str
    criteria: str  # The Instruction (What the user MUST do)
    template_content: str  # The Structure (What the AI enforces)


# --- 2. The Registry ---
TEMPLATES: Dict[str, List[SectionTemplate]] = {
    "Standard Project Charter": [
        {
            "title": "1. Reviewers",
            "criteria": (
                "Reviewers: You must list the name of the Q-PAR (for non-Focus Projects) "
                "or EPQ (for Focus Projects) as a mandatory reviewer. "
                "The author can optionally add additional reviewers."
            ),
            "template_content": (
                "Reviewers: <Add Name of Q-PAR or EPQ> (Mandatory)\n"
                "Additional Reviewers: <Add Optional Name>\n"
                "Approver: <Add Name of Department Head>"
            ),
        },
        {
            "title": "2. Problem Statement",
            "criteria": (
                "Describe the current situation, the specific pain points, and the business impact. "
                "Do not include the solution here. Focus only on the problem."
            ),
            "template_content": (
                "Current Situation: <Describe the process as it exists today>\n\n"
                "Pain Points:\n"
                "1. <Pain Point 1>\n"
                "2. <Pain Point 2>\n\n"
                "Business Impact: <Describe cost, time, or quality loss>"
            ),
        },
        {
            "title": "3. Objectives (SMART)",
            "criteria": (
                "Define SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound). "
                "You MUST include at least one measurable KPI (Key Performance Indicator) and a target date."
            ),
            "template_content": (
                "Goal: <Describe the main goal>\n"
                "KPI: <Measurable Metric> (Current: X -> Target: Y)\n"
                "Target Date: <DD/MM/YYYY>"
            ),
        },
        {
            "title": "4. Risks & Mitigation",
            "criteria": (
                "List at least 2 potential risks to the project success and how you plan to mitigate them."
            ),
            "template_content": (
                "Risk 1: <Description of Risk>\n"
                "Mitigation 1: <Plan to avoid or reduce impact>\n\n"
                "Risk 2: <Description of Risk>\n"
                "Mitigation 2: <Plan to avoid or reduce impact>"
            ),
        },
    ],
    "Simple Document": [
        {
            "title": "1. Executive Summary",
            "criteria": "Provide a high-level summary of the document in under 100 words.",
            "template_content": "<Write summary here>",
        },
        {
            "title": "2. Key Highlights",
            "criteria": "List exactly 3 key takeaways from the meeting or project.",
            "template_content": (
                "1. <Highlight 1>\n2. <Highlight 2>\n3. <Highlight 3>"
            ),
        },
    ],
}

# --- 3. Helper Functions ---


def get_available_templates() -> List[str]:
    """Returns a list of template names for the dropdown."""
    return list(TEMPLATES.keys())


def get_template_sections(template_name: str) -> List[SectionTemplate]:
    """Returns the sections for a specific template name."""
    return TEMPLATES.get(template_name, [])
