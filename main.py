"""
Emergency Response Operation Success Classifier — interactive entry point.

Collects operation details from the user through the terminal and prints
the classification result.

Run with:
    python main.py

For the automated demonstration with pre-set test cases, run:
    python demo.py
"""

import json

from src.classifier import classify
from src.validation.input_validator import (
    InputValidationError,
    ALLOWED_PRIORITIES,
)

HEADER = "=" * 36
DIVIDER = "-" * 36


def print_header() -> None:
    print(f"\n{HEADER}")
    print("  EMERGENCY RESPONSE CLASSIFIER")
    print(f"{HEADER}\n")


def ask_priority() -> str:
    """
    Prompt the user for a case priority.

    Re-prompts on invalid input until an accepted value is entered.
    Returns the normalized (lowercase) priority string.
    """
    allowed = "/".join(sorted(ALLOWED_PRIORITIES))
    prompt = f"Enter case priority ({allowed}): "

    while True:
        raw = input(prompt).strip()
        normalized = raw.lower()

        if normalized in ALLOWED_PRIORITIES:
            return normalized

        print(
            f"  Invalid priority: {raw!r}. "
            f"Please enter one of: {sorted(ALLOWED_PRIORITIES)}.\n"
        )


def ask_response_time() -> str | None:
    """
    Prompt the user for a response time.

    Accepts any non-empty string (e.g. '8 minutes', '45 seconds',
    '00:08:32') or the word 'unknown' or a blank entry (both treated
    as not provided).

    Returns the user's string, or None when unknown / not provided.
    """
    prompt = (
        "Enter response time "
        "(include unit if known, otherwise enter unknown): "
    )
    raw = input(prompt).strip()

    if not raw or raw.lower() == "unknown":
        return None

    return raw


def ask_comments() -> str:
    """
    Prompt the user for officers' comments.

    Re-prompts when the entry is empty or whitespace-only.
    Returns the trimmed comment string.
    """
    prompt = "Enter officers' comments about the operation: "

    while True:
        raw = input(prompt).strip()

        if raw:
            return raw

        print("  Comments cannot be empty. Please describe the operation.\n")


def print_result(result: dict) -> None:
    """Display the classification result."""
    print(f"\n{HEADER}")
    print("             RESULT")
    print(f"{HEADER}\n")
    print(json.dumps(result, indent=2))
    print()


def main() -> None:
    print_header()

    # --- Collect inputs ---
    case_priority = ask_priority()
    response_time = ask_response_time()
    comments = ask_comments()

    # --- Classify ---
    print(f"\n{DIVIDER}")
    print("  Analysing — please wait...")
    print(f"{DIVIDER}")

    try:
        result = classify(
            case_priority=case_priority,
            response_time=response_time,
            officers_comments=comments,
        )
        print_result(result)

    except InputValidationError as err:
        # Should not reach here because ask_priority() already validates,
        # but guard against any future input path that skips it.
        print(f"\n  Input error: {err}\n")

    except RuntimeError as err:
        print(
            f"\n  Classification failed.\n"
            f"  Reason: {err}\n"
            f"\n  Make sure Ollama is running and the 'erss' model is available:\n"
            f"    ollama serve\n"
            f"    ollama list\n"
        )

    except Exception as err:  # pylint: disable=broad-except
        print(f"\n  Unexpected error: {err}\n")


if __name__ == "__main__":
    main()
