"""
Unit tests for the decision engine.

Tests the decision table logic independently of the LLM.
All inputs are deterministic — no Ollama calls are made.

Three valid outcome_achievement values: "achieved", "not_achieved", "unknown".
"partially_achieved" was removed; partial completion is now treated as "unknown".
"""

import pytest

from src.classification.decision_engine import decide


class TestDecideSuccessful:
    """Cases that must return True."""

    def test_achieved_and_timely(self):
        assert decide("achieved", "timely") is True


class TestDecideFailed:
    """Cases that must return False."""

    def test_not_achieved_timely(self):
        assert decide("not_achieved", "timely") is False

    def test_achieved_not_timely(self):
        assert decide("achieved", "not_timely") is False

    def test_not_achieved_not_timely(self):
        assert decide("not_achieved", "not_timely") is False

    def test_not_achieved_unknown_timeliness(self):
        # Outcome is conclusively negative — timeliness does not save it
        assert decide("not_achieved", "unknown") is False

    def test_unknown_outcome_not_timely(self):
        # Timeliness is conclusively negative
        assert decide("unknown", "not_timely") is False


class TestDecideInsufficientInfo:
    """Cases that must return "insufficient_info"."""

    def test_achieved_unknown_timeliness(self):
        assert decide("achieved", "unknown") == "insufficient_info"

    def test_unknown_outcome_timely(self):
        assert decide("unknown", "timely") == "insufficient_info"

    def test_unknown_outcome_unknown_timeliness(self):
        assert decide("unknown", "unknown") == "insufficient_info"


class TestDecideInvalidInputs:
    """Invalid inputs must raise ValueError."""

    def test_invalid_outcome(self):
        with pytest.raises(ValueError, match="Invalid outcome_achievement"):
            decide("success", "timely")

    def test_partially_achieved_now_invalid(self):
        # "partially_achieved" was removed in this revision — must raise
        with pytest.raises(ValueError, match="Invalid outcome_achievement"):
            decide("partially_achieved", "timely")

    def test_invalid_timeliness(self):
        with pytest.raises(ValueError, match="Invalid timeliness"):
            decide("achieved", "on_time")

    def test_both_invalid(self):
        with pytest.raises(ValueError):
            decide("yes", "fast")
