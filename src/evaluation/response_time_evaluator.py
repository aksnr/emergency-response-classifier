"""
Response-time evaluator.

Evaluates whether the response time is compliant with the applicable
official standard for the given case priority.

Design principles:
  - Standards are loaded from src/config/response_time_standards.py.
  - Only verified standards (verified=True) are applied.
  - When no verified standard exists for a priority, compliance is UNKNOWN.
  - Response time is parsed as a numeric value only when a verified standard
    exists and the unit can be determined from the supplied string.
  - The MHA ERSS 2.0 normalization caps are never used as pass/fail limits.
  - Missing response-time input → compliance is UNKNOWN (not "not timely").

Supported time unit strings (case-insensitive):
  - "min", "mins", "minute", "minutes"
  - "sec", "secs", "second", "seconds"
  - "hr", "hrs", "hour", "hours"

If the unit cannot be determined, compliance is UNKNOWN.

Possible timeliness values returned:
    "timely"      — Compliant with verified standard.
    "not_timely"  — Exceeds verified standard.
    "unknown"     — Standard unavailable or unit cannot be determined.
"""

import re

from src.config.response_time_standards import VERIFIED_STANDARDS


# Maps unit tokens to minutes.
_UNIT_TO_MINUTES = {
    "min": 1,
    "mins": 1,
    "minute": 1,
    "minutes": 1,
    "sec": 1 / 60,
    "secs": 1 / 60,
    "second": 1 / 60,
    "seconds": 1 / 60,
    "hr": 60,
    "hrs": 60,
    "hour": 60,
    "hours": 60,
}

ALLOWED_TIMELINESS_VALUES = {"timely", "not_timely", "unknown"}


def evaluate_response_time(
    case_priority: str,
    response_time: str | None,
) -> dict:
    """
    Evaluate response-time timeliness for a given priority.

    Returns:
        {
            "timeliness":          str,          # one of ALLOWED_TIMELINESS_VALUES
            "standard_applied":    dict | None,  # the verified standard used
            "response_time_input": str | None,   # original input, preserved
            "note":                str,          # explanation for the decision
        }
    """
    result_base = {
        "response_time_input": response_time,
        "standard_applied": None,
    }

    # 1. No response time provided → unknown
    if not response_time:
        return {
            **result_base,
            "timeliness": "unknown",
            "note": "Response time was not provided; compliance cannot be assessed.",
        }

    # 2. Look up verified standard for this priority
    standard = VERIFIED_STANDARDS.get(case_priority)

    if not standard or not standard.get("verified", False):
        return {
            **result_base,
            "timeliness": "unknown",
            "note": (
                f"No verified response-time standard is configured for "
                f"priority '{case_priority}'. "
                "Compliance cannot be assessed until an official standard "
                "is added to src/config/response_time_standards.py."
            ),
        }

    # 3. Attempt to parse the response-time value and unit
    parsed = _parse_response_time(response_time)

    if parsed is None:
        return {
            **result_base,
            "timeliness": "unknown",
            "standard_applied": standard,
            "note": (
                f"Could not parse a numeric value and recognised time unit "
                f"from response_time: {response_time!r}. "
                "Compliance cannot be assessed."
            ),
        }

    value_minutes, unit_token = parsed
    max_minutes = standard["max_minutes"]

    if value_minutes <= max_minutes:
        timeliness = "timely"
        note = (
            f"Response time of {response_time!r} ({value_minutes:.2f} min) "
            f"is within the {max_minutes}-minute standard for "
            f"'{case_priority}' priority. Source: {standard['source']}."
        )
    else:
        timeliness = "not_timely"
        note = (
            f"Response time of {response_time!r} ({value_minutes:.2f} min) "
            f"exceeds the {max_minutes}-minute standard for "
            f"'{case_priority}' priority. Source: {standard['source']}."
        )

    return {
        **result_base,
        "timeliness": timeliness,
        "standard_applied": standard,
        "note": note,
    }


def _parse_response_time(response_time: str) -> tuple[float, str] | None:
    """
    Parse a response-time string into (value_in_minutes, unit_token).

    Returns None if parsing fails (unknown format or unit).

    Accepts formats such as:
        "8 minutes", "8min", "90 seconds", "1.5 hours", "8 mins"
    """
    text = response_time.strip().lower()

    # Match optional leading number, optional whitespace, then unit word.
    pattern = r"^(\d+(?:\.\d+)?)\s*([a-z]+)$"
    match = re.match(pattern, text)

    if not match:
        return None

    try:
        numeric_value = float(match.group(1))
    except ValueError:
        return None

    unit_token = match.group(2)
    multiplier = _UNIT_TO_MINUTES.get(unit_token)

    if multiplier is None:
        return None

    return numeric_value * multiplier, unit_token
