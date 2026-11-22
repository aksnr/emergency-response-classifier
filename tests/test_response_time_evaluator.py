"""
Unit tests for the response-time evaluator.

Tests timeliness evaluation logic independently of the LLM.
Covers both the "no verified standard" path (current default) and
the behaviour when a standard is active (via monkeypatching).
"""

import pytest

from src.evaluation import response_time_evaluator as rte
from src.evaluation.response_time_evaluator import evaluate_response_time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_STANDARD = {
    "max_minutes": 10,
    "measurement": "call received → ERU arrival",
    "source": "Test SOP",
    "verified": True,
}


@pytest.fixture()
def with_critical_standard(monkeypatch):
    """Monkeypatch VERIFIED_STANDARDS to include a critical standard."""
    monkeypatch.setattr(
        rte,
        "VERIFIED_STANDARDS",
        {"critical": MOCK_STANDARD},
    )


# ---------------------------------------------------------------------------
# Tests — no verified standard configured (default state)
# ---------------------------------------------------------------------------

class TestNoVerifiedStandard:
    """With an empty VERIFIED_STANDARDS dict, timeliness is always unknown."""

    def test_response_time_provided_no_standard(self):
        result = evaluate_response_time("critical", "8 minutes")
        assert result["timeliness"] == "unknown"
        assert result["standard_applied"] is None

    def test_response_time_missing_no_standard(self):
        result = evaluate_response_time("high", None)
        assert result["timeliness"] == "unknown"

    def test_all_priorities_return_unknown(self):
        for priority in ("critical", "high", "normal"):
            result = evaluate_response_time(priority, "5 minutes")
            assert result["timeliness"] == "unknown"


# ---------------------------------------------------------------------------
# Tests — with a verified standard configured (via monkeypatch)
# ---------------------------------------------------------------------------

class TestWithVerifiedStandard:

    def test_timely_response(self, with_critical_standard):
        result = evaluate_response_time("critical", "8 minutes")
        assert result["timeliness"] == "timely"
        assert result["standard_applied"] == MOCK_STANDARD

    def test_not_timely_response(self, with_critical_standard):
        result = evaluate_response_time("critical", "15 minutes")
        assert result["timeliness"] == "not_timely"

    def test_exactly_at_limit(self, with_critical_standard):
        result = evaluate_response_time("critical", "10 minutes")
        assert result["timeliness"] == "timely"

    def test_seconds_unit(self, with_critical_standard):
        # 540 seconds = 9 minutes → timely (< 10 min)
        result = evaluate_response_time("critical", "540 seconds")
        assert result["timeliness"] == "timely"

    def test_hours_unit(self, with_critical_standard):
        # 1 hour = 60 minutes → not timely
        result = evaluate_response_time("critical", "1 hour")
        assert result["timeliness"] == "not_timely"

    def test_missing_response_time_with_standard(self, with_critical_standard):
        result = evaluate_response_time("critical", None)
        assert result["timeliness"] == "unknown"

    def test_unrecognised_unit(self, with_critical_standard):
        result = evaluate_response_time("critical", "8 km")
        assert result["timeliness"] == "unknown"

    def test_no_unit_string(self, with_critical_standard):
        # Bare number without unit → unknown
        result = evaluate_response_time("critical", "8")
        assert result["timeliness"] == "unknown"

    def test_priority_without_standard(self, with_critical_standard):
        # "high" has no standard even though "critical" does
        result = evaluate_response_time("high", "8 minutes")
        assert result["timeliness"] == "unknown"

    def test_response_time_input_preserved(self, with_critical_standard):
        result = evaluate_response_time("critical", "8 minutes")
        assert result["response_time_input"] == "8 minutes"
