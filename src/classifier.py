"""
Emergency Response Operation Success Classifier.

Public interface: classify()

Accepts:
    case_priority       : "critical" | "high" | "normal"
    response_time       : free-text string, e.g. "8 minutes" (or None)
    officers_comments   : free-text string (or None)

Returns:
    {"is_success": True}
    {"is_success": False}
    {"is_success": "insufficient_info"}
"""

from src.validation.input_validator import validate_inputs, InputValidationError
from src.analysis.comments_analyzer import CommentsAnalyzer
from src.evaluation.response_time_evaluator import evaluate_response_time
from src.classification.decision_engine import decide


def classify(
    case_priority: str,
    response_time: str | None,
    officers_comments: str | None,
    llm_model: str = "erss",
) -> dict:
    """
    Classify an emergency response operation.

    Parameters
    ----------
    case_priority : str
        Priority level: "critical", "high", or "normal".
    response_time : str | None
        Response time as supplied (e.g. "8 minutes"). None = not known.
    officers_comments : str | None
        Free-text operational comments. None = not provided.
    llm_model : str
        Ollama model name to use for comments analysis.

    Returns
    -------
    dict
        {"is_success": True | False | "insufficient_info"}

    Raises
    ------
    InputValidationError
        When case_priority is invalid or other required inputs fail validation.
    RuntimeError
        When the LLM call fails.
    """
    # Step 1 — Validate and normalize inputs
    inputs = validate_inputs(case_priority, response_time, officers_comments)

    # Step 2 — Analyze officers' comments with LLM
    analyzer = CommentsAnalyzer(model=llm_model)
    analysis = analyzer.analyze(inputs["officers_comments"])
    outcome_achievement = analysis["outcome_achievement"]

    # Step 3 — Evaluate response-time compliance (deterministic)
    time_eval = evaluate_response_time(
        case_priority=inputs["case_priority"],
        response_time=inputs["response_time"],
    )
    timeliness = time_eval["timeliness"]

    # Step 4 — Apply decision table
    is_success = decide(outcome_achievement, timeliness)

    # Step 5 — Return validated output (only is_success field)
    return {"is_success": is_success}
