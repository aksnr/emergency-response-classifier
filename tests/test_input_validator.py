"""
Unit tests for input validation.

Tests validate_inputs() independently of any LLM or Ollama calls.
"""

import pytest

from src.validation.input_validator import validate_inputs, InputValidationError


class TestPriorityValidation:
    """case_priority must be one of critical, high, normal."""

    def test_critical_accepted(self):
        result = validate_inputs("critical", "8 minutes", "Officers responded.")
        assert result["case_priority"] == "critical"

    def test_high_accepted(self):
        result = validate_inputs("high", None, None)
        assert result["case_priority"] == "high"

    def test_normal_accepted(self):
        result = validate_inputs("normal", "5 minutes", None)
        assert result["case_priority"] == "normal"

    def test_case_insensitive(self):
        result = validate_inputs("CRITICAL", "8 minutes", None)
        assert result["case_priority"] == "critical"

    def test_whitespace_stripped(self):
        result = validate_inputs("  high  ", None, None)
        assert result["case_priority"] == "high"

    def test_invalid_priority_urgent(self):
        with pytest.raises(InputValidationError, match="Invalid case_priority"):
            validate_inputs("urgent", "8 minutes", "Comments here.")

    def test_invalid_priority_low(self):
        with pytest.raises(InputValidationError, match="Invalid case_priority"):
            validate_inputs("low", "5 minutes", None)

    def test_empty_priority(self):
        with pytest.raises(InputValidationError):
            validate_inputs("", "8 minutes", None)

    def test_none_priority(self):
        with pytest.raises(InputValidationError):
            validate_inputs(None, "8 minutes", None)

    def test_numeric_priority(self):
        with pytest.raises(InputValidationError):
            validate_inputs(1, "8 minutes", None)


class TestResponseTimeValidation:
    """response_time is preserved as-is; None/blank → None."""

    def test_string_preserved(self):
        result = validate_inputs("critical", "8 minutes", None)
        assert result["response_time"] == "8 minutes"

    def test_none_becomes_none(self):
        result = validate_inputs("high", None, None)
        assert result["response_time"] is None

    def test_blank_string_becomes_none(self):
        result = validate_inputs("high", "   ", None)
        assert result["response_time"] is None

    def test_unknown_unit_string_preserved(self):
        # Must not raise — unit parsing is not done here
        result = validate_inputs("high", "unknown", None)
        assert result["response_time"] == "unknown"

    def test_numeric_only_preserved(self):
        # Bare number is accepted; unit is unknown — evaluator handles it
        result = validate_inputs("critical", "10", None)
        assert result["response_time"] == "10"


class TestOfficersCommentsValidation:
    """officers_comments is preserved as-is; None/blank → None."""

    def test_string_preserved(self):
        result = validate_inputs("high", None, "Officers arrived on time.")
        assert result["officers_comments"] == "Officers arrived on time."

    def test_none_becomes_none(self):
        result = validate_inputs("high", None, None)
        assert result["officers_comments"] is None

    def test_blank_string_becomes_none(self):
        result = validate_inputs("critical", "8 minutes", "   ")
        assert result["officers_comments"] is None
