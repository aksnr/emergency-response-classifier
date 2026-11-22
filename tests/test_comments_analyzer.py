"""
Unit tests for CommentsAnalyzer.

The LLM is mocked throughout — no Ollama calls are made.

Two test groups:
  1. Parsing and validation — verifies the analyzer correctly handles valid
     and invalid JSON responses from the model.
  2. Scenario routing — verifies that the five specified comment scenarios
     produce the correct outcome_achievement when the mocked LLM returns the
     expected value. These tests also confirm the full pipeline decision
     (via decide()) for each scenario, using the current default where
     no verified response-time standard exists (timeliness → "unknown").
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.analysis.comments_analyzer import CommentsAnalyzer, ALLOWED_OUTCOME_VALUES
from src.classification.decision_engine import decide


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_llm_response(outcome: str, evidence: str = "Test evidence.") -> str:
    """Return a JSON string as the mocked LLM would produce."""
    return json.dumps({
        "outcome_achievement": outcome,
        "evidence_summary": evidence,
    })


def analyzer_with_mock_llm(llm_response: str) -> CommentsAnalyzer:
    """Return a CommentsAnalyzer whose LLM client is mocked."""
    analyzer = CommentsAnalyzer(model="erss")
    analyzer.llm.generate = MagicMock(return_value=llm_response)
    return analyzer


# ---------------------------------------------------------------------------
# 1. Parsing and validation tests (no real LLM)
# ---------------------------------------------------------------------------

class TestParseAndValidate:

    def test_valid_achieved_response(self):
        analyzer = analyzer_with_mock_llm(make_llm_response("achieved"))
        result = analyzer.analyze("The team rescued the person.")
        assert result["outcome_achievement"] == "achieved"
        assert isinstance(result["evidence_summary"], str)

    def test_valid_not_achieved_response(self):
        analyzer = analyzer_with_mock_llm(make_llm_response("not_achieved"))
        result = analyzer.analyze("The suspect escaped before officers arrived.")
        assert result["outcome_achievement"] == "not_achieved"

    def test_valid_unknown_response(self):
        analyzer = analyzer_with_mock_llm(make_llm_response("unknown"))
        result = analyzer.analyze("Team was deployed to the reported location.")
        assert result["outcome_achievement"] == "unknown"

    def test_no_comments_skips_llm_returns_unknown(self):
        """When comments are None, the LLM must not be called."""
        analyzer = CommentsAnalyzer(model="erss")
        analyzer.llm.generate = MagicMock(side_effect=AssertionError("LLM should not be called"))
        result = analyzer.analyze(None)
        assert result["outcome_achievement"] == "unknown"
        analyzer.llm.generate.assert_not_called()

    def test_empty_string_comments_skips_llm(self):
        analyzer = CommentsAnalyzer(model="erss")
        analyzer.llm.generate = MagicMock(side_effect=AssertionError("LLM should not be called"))
        result = analyzer.analyze("   ")
        # Input validator converts blank to None; analyzer receives None
        # But CommentsAnalyzer.analyze() also guards against falsy values
        result2 = analyzer.analyze(None)
        assert result2["outcome_achievement"] == "unknown"

    def test_invalid_json_raises_value_error(self):
        analyzer = analyzer_with_mock_llm("not valid json at all")
        with pytest.raises(ValueError, match="invalid JSON"):
            analyzer.analyze("Some comments.")

    def test_non_dict_json_raises_value_error(self):
        analyzer = analyzer_with_mock_llm('["achieved"]')
        with pytest.raises(ValueError, match="JSON object"):
            analyzer.analyze("Some comments.")

    def test_disallowed_outcome_value_raises(self):
        analyzer = analyzer_with_mock_llm(make_llm_response("partially_achieved"))
        with pytest.raises(ValueError, match="unexpected outcome_achievement"):
            analyzer.analyze("Some comments.")

    def test_missing_outcome_field_raises(self):
        bad_response = json.dumps({"evidence_summary": "nothing here"})
        analyzer = analyzer_with_mock_llm(bad_response)
        with pytest.raises(ValueError, match="unexpected outcome_achievement"):
            analyzer.analyze("Some comments.")

    def test_non_string_evidence_coerced_to_string(self):
        response = json.dumps({"outcome_achievement": "unknown", "evidence_summary": 42})
        analyzer = analyzer_with_mock_llm(response)
        result = analyzer.analyze("Some comments.")
        assert result["evidence_summary"] == "42"

    def test_allowed_outcome_values_are_exactly_three(self):
        assert ALLOWED_OUTCOME_VALUES == {"achieved", "not_achieved", "unknown"}


# ---------------------------------------------------------------------------
# 2. Scenario routing tests
#    Verifies: given specific comments, the LLM should return a specific
#    outcome, and the full pipeline should produce the correct is_success.
#
#    The mocked LLM returns the expected outcome for each scenario.
#    Timeliness is "unknown" (no verified standard configured) so the
#    decision follows: achieved+unknown → insufficient_info,
#    not_achieved+(any) → false, unknown+(any except not_timely) → insufficient_info.
# ---------------------------------------------------------------------------

class TestCommentScenarios:
    """
    Each test specifies:
      - The comment text (what an officer might write)
      - The correct outcome_achievement the LLM should produce
      - The expected final is_success given timeliness="unknown"
    """

    def _run(self, comment: str, expected_outcome: str) -> dict:
        """Analyze comment with mocked LLM returning expected_outcome."""
        analyzer = analyzer_with_mock_llm(make_llm_response(expected_outcome))
        result = analyzer.analyze(comment)
        assert result["outcome_achievement"] == expected_outcome
        is_success = decide(expected_outcome, "unknown")
        return {"outcome_achievement": result["outcome_achievement"], "is_success": is_success}

    def test_deployment_only_is_unknown(self):
        """
        'Team was deployed to the reported location.'
        Deployment establishes neither success nor failure → unknown.
        With timeliness unknown: → insufficient_info.
        """
        r = self._run(
            "Team was deployed to the reported location.",
            "unknown",
        )
        assert r["outcome_achievement"] == "unknown"
        assert r["is_success"] == "insufficient_info"

    def test_arrival_and_searching_is_unknown(self):
        """
        'Team reached the location and started searching.'
        Arrival + an action without a final outcome → unknown.
        With timeliness unknown: → insufficient_info.
        """
        r = self._run(
            "Team reached the location and started searching.",
            "unknown",
        )
        assert r["outcome_achievement"] == "unknown"
        assert r["is_success"] == "insufficient_info"

    def test_successful_reunion_is_achieved(self):
        """
        'The missing person was located and reunited with family.'
        Explicit positive outcome → achieved.
        With timeliness unknown: → insufficient_info (standard not configured).
        """
        r = self._run(
            "The missing person was located and reunited with family.",
            "achieved",
        )
        assert r["outcome_achievement"] == "achieved"
        assert r["is_success"] == "insufficient_info"

    def test_search_terminated_not_found_is_not_achieved(self):
        """
        'The person could not be located and the search was terminated.'
        Explicit negative outcome → not_achieved.
        With any timeliness: → false (conclusive negative).
        """
        r = self._run(
            "The person could not be located and the search was terminated.",
            "not_achieved",
        )
        assert r["outcome_achievement"] == "not_achieved"
        assert r["is_success"] is False

    def test_ongoing_operation_is_unknown(self):
        """
        'Operation is still ongoing.'
        No final outcome has been reached → unknown.
        With timeliness unknown: → insufficient_info.
        """
        r = self._run(
            "Operation is still ongoing.",
            "unknown",
        )
        assert r["outcome_achievement"] == "unknown"
        assert r["is_success"] == "insufficient_info"
