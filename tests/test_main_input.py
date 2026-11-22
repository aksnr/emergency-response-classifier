"""
Unit tests for the interactive input functions in main.py.

All tests use unittest.mock.patch to simulate keyboard input.
No LLM or Ollama calls are made.
"""

from unittest.mock import patch

import pytest

from main import ask_priority, ask_response_time, ask_comments


# ---------------------------------------------------------------------------
# ask_priority
# ---------------------------------------------------------------------------

class TestAskPriority:

    def test_critical_accepted(self):
        with patch("builtins.input", return_value="critical"):
            assert ask_priority() == "critical"

    def test_high_accepted(self):
        with patch("builtins.input", return_value="high"):
            assert ask_priority() == "high"

    def test_normal_accepted(self):
        with patch("builtins.input", return_value="normal"):
            assert ask_priority() == "normal"

    def test_uppercase_normalized(self):
        with patch("builtins.input", return_value="CRITICAL"):
            assert ask_priority() == "critical"

    def test_mixed_case_normalized(self):
        with patch("builtins.input", return_value="High"):
            assert ask_priority() == "high"

    def test_whitespace_stripped(self):
        with patch("builtins.input", return_value="  normal  "):
            assert ask_priority() == "normal"

    def test_invalid_then_valid(self):
        """Invalid input is rejected; the second attempt is accepted."""
        with patch("builtins.input", side_effect=["urgent", "critical"]):
            assert ask_priority() == "critical"

    def test_multiple_invalid_then_valid(self):
        with patch("builtins.input", side_effect=["low", "emergency", "HIGH", "high"]):
            assert ask_priority() == "high"

    def test_invalid_input_does_not_raise(self):
        """Invalid priority must not raise; it must loop and retry."""
        with patch("builtins.input", side_effect=["bad", "normal"]):
            result = ask_priority()
        assert result == "normal"


# ---------------------------------------------------------------------------
# ask_response_time
# ---------------------------------------------------------------------------

class TestAskResponseTime:

    def test_minutes_string_preserved(self):
        with patch("builtins.input", return_value="8 minutes"):
            assert ask_response_time() == "8 minutes"

    def test_seconds_string_preserved(self):
        with patch("builtins.input", return_value="45 seconds"):
            assert ask_response_time() == "45 seconds"

    def test_timestamp_format_preserved(self):
        with patch("builtins.input", return_value="00:08:32"):
            assert ask_response_time() == "00:08:32"

    def test_unknown_keyword_returns_none(self):
        with patch("builtins.input", return_value="unknown"):
            assert ask_response_time() is None

    def test_unknown_uppercase_returns_none(self):
        with patch("builtins.input", return_value="UNKNOWN"):
            assert ask_response_time() is None

    def test_blank_input_returns_none(self):
        with patch("builtins.input", return_value=""):
            assert ask_response_time() is None

    def test_whitespace_only_returns_none(self):
        with patch("builtins.input", return_value="   "):
            assert ask_response_time() is None

    def test_arbitrary_string_preserved(self):
        """Any non-empty, non-'unknown' string must be passed through unchanged."""
        with patch("builtins.input", return_value="approximately 10 mins"):
            assert ask_response_time() == "approximately 10 mins"


# ---------------------------------------------------------------------------
# ask_comments
# ---------------------------------------------------------------------------

class TestAskComments:

    def test_valid_comment_returned(self):
        with patch("builtins.input", return_value="Officers secured the perimeter."):
            assert ask_comments() == "Officers secured the perimeter."

    def test_leading_trailing_whitespace_stripped(self):
        with patch("builtins.input", return_value="  Team arrived on scene.  "):
            assert ask_comments() == "Team arrived on scene."

    def test_empty_then_valid(self):
        """Empty input is rejected; second attempt is accepted."""
        with patch("builtins.input", side_effect=["", "The suspect was apprehended."]):
            assert ask_comments() == "The suspect was apprehended."

    def test_whitespace_only_then_valid(self):
        with patch("builtins.input", side_effect=["   ", "Operation completed successfully."]):
            assert ask_comments() == "Operation completed successfully."

    def test_multiple_empty_then_valid(self):
        with patch("builtins.input", side_effect=["", "  ", "\t", "Officers responded."]):
            assert ask_comments() == "Officers responded."

    def test_empty_does_not_raise(self):
        """Empty input must not raise; it must loop and retry."""
        with patch("builtins.input", side_effect=["", "valid comment"]):
            result = ask_comments()
        assert result == "valid comment"
