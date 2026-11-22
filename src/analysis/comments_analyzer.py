"""
Officers' comments analyzer.

Uses the local Ollama LLM to interpret free-text officers' comments and
determine the outcome achievement dimension of the classifier.

The LLM is asked only about what happened — did the response team achieve
the operation's objective? It is never asked to judge timeliness or to
produce the final classification.

Exactly three internal outcome states are supported:

    "achieved"      — The comments contain explicit, positive evidence that
                      the operation's objective was fully completed.
                      Example: "rescued the person", "fire extinguished",
                      "suspect arrested", "missing child located and reunited".

    "not_achieved"  — The comments contain explicit, negative evidence that
                      the objective failed or could not be completed.
                      Example: "suspect escaped", "search terminated — person
                      not found", "rescue unsuccessful", "operation abandoned".

    "unknown"       — The comments describe deployment, arrival, attendance,
                      ongoing operations, partial actions, or events without
                      establishing the final outcome. Also used when comments
                      are contradictory, vague, or absent.
                      Example: "team was deployed", "officers reached the
                      scene", "search is ongoing", "team started operations".

IMPORTANT: missing evidence of success is NOT evidence of failure.
Use "not_achieved" only when failure is explicitly stated.
"""

import json

from src.llm.llama_client import OllamaClient


ANALYSIS_SYSTEM_PROMPT = """You are an evidence analyst for emergency response operations.

Your task is to read officers' comments and determine whether the emergency response team achieved the operation's objective.

You must return exactly one of three values for outcome_achievement:

  "achieved"     — Use ONLY when the comments contain explicit, positive evidence
                   that the operation's objective was fully completed.
                   Examples: "rescued the person", "suspect arrested",
                   "missing child located and reunited with family",
                   "fire was extinguished and all occupants were safely evacuated".

  "not_achieved" — Use ONLY when the comments contain explicit, negative evidence
                   that the objective failed or could not be completed.
                   Examples: "suspect had already fled", "search was terminated —
                   person not found", "rescue was unsuccessful", "operation abandoned".

  "unknown"      — Use for ALL other cases, including:
                   * Deployment or arrival only ("team was deployed", "officers reached the scene")
                   * Ongoing operations ("search is ongoing", "operation is still ongoing")
                   * Actions without a stated final outcome ("team started searching")
                   * Ambiguous or vague comments
                   * Contradictory statements
                   * No comments provided

CRITICAL RULES:
- Missing evidence of success is NOT evidence of failure. Do not return "not_achieved"
  just because success is not mentioned.
- Deployment, arrival, or attendance alone does not prove success or failure.
  Return "unknown" for these.
- Base your answer only on what is explicitly stated in the comments.
- Do not invent facts or infer outcomes not stated.
- Do not use response time or priority in your reasoning.

Return exactly this JSON structure and nothing else:

{
    "outcome_achievement": "<achieved|not_achieved|unknown>",
    "evidence_summary": "<one sentence explaining the key evidence>"
}"""

ALLOWED_OUTCOME_VALUES = {
    "achieved",
    "not_achieved",
    "unknown",
}


class CommentsAnalyzer:
    """Analyzes officers' comments using the local LLM."""

    def __init__(self, model: str = "erss"):
        self.llm = OllamaClient(model=model)

    def analyze(self, officers_comments: str | None) -> dict:
        """
        Analyze officers' comments and return outcome achievement evidence.

        Returns:
            {
                "outcome_achievement": str,   # one of ALLOWED_OUTCOME_VALUES
                "evidence_summary":    str,
            }

        If comments are None or empty, returns outcome_achievement = "unknown"
        without calling the LLM.
        """
        if not officers_comments or not officers_comments.strip():
            return {
                "outcome_achievement": "unknown",
                "evidence_summary": "No officers' comments were provided.",
            }

        prompt = f"""Analyze these officers' comments from an emergency response operation.

OFFICERS' COMMENTS:
{officers_comments}

Determine whether the response team achieved the operation's objective.
Return only the JSON as instructed."""

        try:
            raw_response = self.llm.generate(
                prompt=prompt,
                system_prompt=ANALYSIS_SYSTEM_PROMPT,
                format="json",
            )
        except RuntimeError as error:
            raise RuntimeError(
                f"LLM call failed during comments analysis: {error}"
            ) from error

        return self._parse_and_validate(raw_response)

    def _parse_and_validate(self, raw_response: str) -> dict:
        """Parse and validate the LLM JSON response."""
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Comments analyzer received invalid JSON from model: "
                f"{raw_response!r}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError(
                "Comments analyzer expected a JSON object from the model."
            )

        outcome = data.get("outcome_achievement")
        if outcome not in ALLOWED_OUTCOME_VALUES:
            raise ValueError(
                f"Comments analyzer received unexpected outcome_achievement "
                f"value: {outcome!r}. "
                f"Allowed: {sorted(ALLOWED_OUTCOME_VALUES)}."
            )

        evidence = data.get("evidence_summary", "")
        if not isinstance(evidence, str):
            evidence = str(evidence)

        return {
            "outcome_achievement": outcome,
            "evidence_summary": evidence,
        }
