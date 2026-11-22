"""
Emergency Response Operation Success Classifier — demonstration script.

Runs a fixed set of pre-configured scenarios without requiring user input.
Useful for verifying that the classifier produces the expected outputs after
any code changes.

Run with:
    python demo.py

For interactive use, run:
    python main.py
"""

import json

from src.classifier import classify
from src.validation.input_validator import InputValidationError


def run_demo(label: str, **kwargs) -> None:
    """Run a single classification and print the result."""
    print(f"\n{'─' * 60}")
    print(f"Demo: {label}")
    print("Input:")
    print(f"  case_priority    : {kwargs.get('case_priority')!r}")
    print(f"  response_time    : {kwargs.get('response_time')!r}")
    print(f"  officers_comments: {kwargs.get('officers_comments')!r}")
    print("Result:")
    try:
        result = classify(**kwargs)
        print(json.dumps(result, indent=4))
    except InputValidationError as err:
        print(f"  Validation error: {err}")
    except RuntimeError as err:
        print(f"  Runtime error   : {err}")


def main() -> None:
    print("Emergency Response Operation Success Classifier — Demo")
    print("=" * 60)

    # Demo 1: Successful rescue (insufficient_info until verified
    #         response-time standards are configured)
    run_demo(
        label="Successful rescue — response time standard not yet verified",
        case_priority="critical",
        response_time="8 minutes",
        officers_comments=(
            "The response team reached the location and successfully "
            "rescued the person. The victim was handed over to the "
            "medical team in stable condition."
        ),
    )

    # Demo 2: Unsuccessful — objective not achieved
    run_demo(
        label="Unsuccessful — suspect escaped before officers arrived",
        case_priority="high",
        response_time="12 minutes",
        officers_comments=(
            "Officers arrived at the scene but the suspect had already fled "
            "before the team reached the location. No arrest was made."
        ),
    )

    # Demo 3: Insufficient information — deployment only
    run_demo(
        label="Insufficient information — deployment only",
        case_priority="normal",
        response_time="5 minutes",
        officers_comments="Team was deployed to the reported location.",
    )

    # Demo 4: Invalid priority (validation error)
    run_demo(
        label="Invalid priority value (validation error expected)",
        case_priority="urgent",
        response_time="10 minutes",
        officers_comments="Officers responded to the call.",
    )

    # Demo 5: Missing response time and comments
    run_demo(
        label="Missing response time and comments",
        case_priority="high",
        response_time=None,
        officers_comments=None,
    )

    print(f"\n{'─' * 60}")
    print(
        "\nNOTE: When no verified response-time standard is configured for "
        "the given priority,\ntimeliness is always 'unknown'. An operation "
        "can only be classified as 'true'\nwhen BOTH outcome achievement AND "
        "timeliness are confirmed.\nSee src/config/response_time_standards.py "
        "to add a verified standard."
    )


if __name__ == "__main__":
    main()
