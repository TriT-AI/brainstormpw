"""
Unit tests for backend/models.py - Pydantic models and TypedDict definitions.
"""
import pytest
from pydantic import ValidationError

from backend.models import (
    Issue,
    AuditResponse,
    GlobalIssue,
    ConsistencyResponse,
    FixResponse,
    AgentState,
)


class TestIssueModel:
    """Tests for the Issue Pydantic model."""

    @pytest.mark.unit
    def test_issue_valid_creation(self):
        """Test creating a valid Issue instance."""
        issue = Issue(
            id="1",
            severity="High",
            issue_description="Missing required field",
            recommendation="Add the required field",
            fixable=False
        )
        assert issue.id == "1"
        assert issue.severity == "High"
        assert issue.issue_description == "Missing required field"
        assert issue.recommendation == "Add the required field"
        assert issue.fixable is False

    @pytest.mark.unit
    def test_issue_all_severity_levels(self):
        """Test that all severity levels are accepted."""
        for severity in ["High", "Medium", "Low"]:
            issue = Issue(
                id="1",
                severity=severity,
                issue_description="Test issue",
                recommendation="Test recommendation",
                fixable=True
            )
            assert issue.severity == severity

    @pytest.mark.unit
    def test_issue_fixable_true(self):
        """Test Issue with fixable=True."""
        issue = Issue(
            id="2",
            severity="Low",
            issue_description="Formatting issue",
            recommendation="Reformat text",
            fixable=True
        )
        assert issue.fixable is True

    @pytest.mark.unit
    def test_issue_model_dump(self):
        """Test that Issue can be serialized to dict."""
        issue = Issue(
            id="1",
            severity="Medium",
            issue_description="Test",
            recommendation="Fix it",
            fixable=False
        )
        data = issue.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == "1"
        assert data["severity"] == "Medium"

    @pytest.mark.unit
    def test_issue_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Issue(
                id="1",
                severity="High",
                # Missing issue_description
                recommendation="Fix it",
                fixable=False
            )


class TestAuditResponseModel:
    """Tests for the AuditResponse Pydantic model."""

    @pytest.mark.unit
    def test_audit_response_compliant(self):
        """Test creating a compliant AuditResponse."""
        response = AuditResponse(is_compliant=True, issues=[])
        assert response.is_compliant is True
        assert response.issues == []

    @pytest.mark.unit
    def test_audit_response_with_issues(self):
        """Test creating AuditResponse with issues."""
        issue = Issue(
            id="1",
            severity="High",
            issue_description="Problem found",
            recommendation="Fix it",
            fixable=False
        )
        response = AuditResponse(is_compliant=False, issues=[issue])
        assert response.is_compliant is False
        assert len(response.issues) == 1
        assert response.issues[0].id == "1"

    @pytest.mark.unit
    def test_audit_response_default_empty_issues(self):
        """Test that issues defaults to empty list."""
        response = AuditResponse(is_compliant=True)
        assert response.issues == []

    @pytest.mark.unit
    def test_audit_response_multiple_issues(self):
        """Test AuditResponse with multiple issues."""
        issues = [
            Issue(id="1", severity="High", issue_description="Issue 1", recommendation="Fix 1", fixable=False),
            Issue(id="2", severity="Medium", issue_description="Issue 2", recommendation="Fix 2", fixable=True),
            Issue(id="3", severity="Low", issue_description="Issue 3", recommendation="Fix 3", fixable=True),
        ]
        response = AuditResponse(is_compliant=False, issues=issues)
        assert len(response.issues) == 3


class TestGlobalIssueModel:
    """Tests for the GlobalIssue Pydantic model."""

    @pytest.mark.unit
    def test_global_issue_valid_creation(self):
        """Test creating a valid GlobalIssue."""
        issue = GlobalIssue(
            id="G-1",
            title="Contradiction found",
            description="Goal does not match problem",
            related_sections=["Problem Statement", "Objectives"]
        )
        assert issue.id == "G-1"
        assert issue.title == "Contradiction found"
        assert len(issue.related_sections) == 2

    @pytest.mark.unit
    def test_global_issue_empty_sections(self):
        """Test GlobalIssue with empty related_sections."""
        issue = GlobalIssue(
            id="G-1",
            title="General issue",
            description="Document-wide problem",
            related_sections=[]
        )
        assert issue.related_sections == []


class TestConsistencyResponseModel:
    """Tests for the ConsistencyResponse Pydantic model."""

    @pytest.mark.unit
    def test_consistency_response_consistent(self):
        """Test creating a consistent response."""
        response = ConsistencyResponse(is_consistent=True, global_issues=[])
        assert response.is_consistent is True
        assert response.global_issues == []

    @pytest.mark.unit
    def test_consistency_response_with_issues(self):
        """Test ConsistencyResponse with global issues."""
        issue = GlobalIssue(
            id="G-1",
            title="Logic error",
            description="Sections contradict each other",
            related_sections=["Section 1", "Section 2"]
        )
        response = ConsistencyResponse(is_consistent=False, global_issues=[issue])
        assert response.is_consistent is False
        assert len(response.global_issues) == 1


class TestFixResponseModel:
    """Tests for the FixResponse Pydantic model."""

    @pytest.mark.unit
    def test_fix_response_valid(self):
        """Test creating a valid FixResponse."""
        response = FixResponse(fixed_content="Reviewers: John Doe (Q-PAR)")
        assert response.fixed_content == "Reviewers: John Doe (Q-PAR)"

    @pytest.mark.unit
    def test_fix_response_multiline_content(self):
        """Test FixResponse with multiline content."""
        content = """Reviewers: John Doe (Q-PAR)
Additional Reviewers: Jane Smith
Approver: Bob Johnson"""
        response = FixResponse(fixed_content=content)
        assert "John Doe" in response.fixed_content
        assert "Jane Smith" in response.fixed_content


class TestAgentState:
    """Tests for the AgentState TypedDict."""

    @pytest.mark.unit
    def test_agent_state_structure(self):
        """Test that AgentState has expected keys."""
        state: AgentState = {
            "section_title": "Test Section",
            "criteria": "Test criteria",
            "template_structure": "Test structure",
            "user_content": "Test content",
            "issues": [],
            "is_compliant": True,
            "target_issue": None
        }
        assert state["section_title"] == "Test Section"
        assert state["criteria"] == "Test criteria"
        assert state["is_compliant"] is True
        assert state["target_issue"] is None

    @pytest.mark.unit
    def test_agent_state_with_issues(self):
        """Test AgentState with issues populated."""
        state: AgentState = {
            "section_title": "Reviewers",
            "criteria": "Must include name",
            "template_structure": "<Name>",
            "user_content": "",
            "issues": [{"id": "1", "severity": "High"}],
            "is_compliant": False,
            "target_issue": {"id": "1", "severity": "High"}
        }
        assert len(state["issues"]) == 1
        assert state["target_issue"] is not None
