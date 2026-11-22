"""
Input validation for the emergency response classifier.

Validates the three classifier inputs:
  - case_priority   : must be one of the allowed priority levels.
  - response_time   : free-form string; may be null/empty (treated as unknown).
  - officers_comments: free-form text; may be null/empty (treated as unknown).

Validation deliberately avoids assuming any unit or threshold for response_time.
"""

ALLOWED_PRIORITIES = {"critical", "high", "normal"}


class InputValidationError(ValueError):
    """Raised when a classifier input fails validation."""


def validate_inputs(
    case_priority: str,
    response_time: str | None,
    officers_comments: str | None,
) -> dict:
    """
    Validate and normalize classifier inputs.

    Returns a dict with cleaned values:
        {
            "case_priority":    str,
            "response_time":    str | None,   # None when missing / unknown
            "officers_comments": str | None,  # None when missing / unknown
        }

    Raises InputValidationError for invalid inputs.
    """
    # --- case_priority ---
    if not isinstance(case_priority, str) or not case_priority.strip():
        raise InputValidationError(
            "case_priority is required and must be a non-empty string."
        )

    normalized_priority = case_priority.strip().lower()

    if normalized_priority not in ALLOWED_PRIORITIES:
        raise InputValidationError(
            f"Invalid case_priority: {case_priority!r}. "
            f"Allowed values: {sorted(ALLOWED_PRIORITIES)}."
        )

    # --- response_time ---
    # Accept any non-empty string; treat blank / None as unknown.
    # Do NOT parse, convert, or assume units.
    if isinstance(response_time, str) and response_time.strip():
        cleaned_response_time = response_time.strip()
    else:
        cleaned_response_time = None   # unknown / not provided

    # --- officers_comments ---
    # Accept any non-empty string; treat blank / None as unknown.
    if isinstance(officers_comments, str) and officers_comments.strip():
        cleaned_comments = officers_comments.strip()
    else:
        cleaned_comments = None   # unknown / not provided

    return {
        "case_priority": normalized_priority,
        "response_time": cleaned_response_time,
        "officers_comments": cleaned_comments,
    }
