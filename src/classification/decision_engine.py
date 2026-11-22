"""
Decision engine — final classification logic.

Combines outcome_achievement and timeliness to produce one of:
    True               — Operation is successful.
    False              — Operation is unsuccessful.
    "insufficient_info"— Insufficient information to decide.

Three outcome_achievement states are supported:
    "achieved"      — Explicit positive evidence the objective was completed.
    "not_achieved"  — Explicit negative evidence the objective failed.
    "unknown"       — Deployment/arrival/ongoing/no outcome established.

Decision table:
┌─────────────────────┬──────────────────────┬─────────────────────┐
│ outcome_achievement │ timeliness           │ classification      │
├─────────────────────┼──────────────────────┼─────────────────────┤
│ achieved            │ timely               │ True                │
│ not_achieved        │ (any)                │ False  (conclusive) │
│ achieved            │ not_timely           │ False  (conclusive) │
│ unknown             │ not_timely           │ False  (conclusive) │
│ achieved            │ unknown              │ "insufficient_info" │
│ unknown             │ timely               │ "insufficient_info" │
│ unknown             │ unknown              │ "insufficient_info" │
└─────────────────────┴──────────────────────┴─────────────────────┘

Key principle: if either dimension is conclusively negative, classify False
even when the other dimension is unknown.
"""

VALID_OUTCOMES = {"achieved", "not_achieved", "unknown"}
VALID_TIMELINESS = {"timely", "not_timely", "unknown"}


def decide(outcome_achievement: str, timeliness: str) -> bool | str:
    """
    Apply the decision table and return the final classification.

    Parameters
    ----------
    outcome_achievement : str
        One of "achieved", "not_achieved", "unknown".
    timeliness : str
        One of "timely", "not_timely", "unknown".

    Returns
    -------
    True, False, or the string "insufficient_info".

    Raises
    ------
    ValueError
        If either input is not a recognised value.
    """
    if outcome_achievement not in VALID_OUTCOMES:
        raise ValueError(
            f"Invalid outcome_achievement: {outcome_achievement!r}. "
            f"Allowed: {sorted(VALID_OUTCOMES)}."
        )
    if timeliness not in VALID_TIMELINESS:
        raise ValueError(
            f"Invalid timeliness: {timeliness!r}. "
            f"Allowed: {sorted(VALID_TIMELINESS)}."
        )

    oa = outcome_achievement
    tl = timeliness

    # --- Conclusively negative on outcome → always False ---
    if oa == "not_achieved":
        return False

    # --- Conclusively negative on timeliness → always False ---
    if tl == "not_timely":
        return False

    # --- Both positive → Success ---
    if oa == "achieved" and tl == "timely":
        return True

    # --- All remaining combinations are insufficient_info ---
    # Covers: achieved+unknown, unknown+timely, unknown+unknown.
    return "insufficient_info"
