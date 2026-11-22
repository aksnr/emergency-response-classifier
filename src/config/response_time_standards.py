"""
Response-time standards configuration.

IMPORTANT — Read before modifying this file
============================================
The MHA ERSS 2.0 Guidelines (January 2026) define normalization caps of:
  - 5 minutes  : call-taker stage   (call attended → service delivery)
  - 5 minutes  : dispatcher stage   (event read → service delivery)
  - 50 minutes : ERU stage          (service accepted → vehicle at scene)

These caps are used only for performance reporting and benchmarking.
They are NOT individual-operation pass/fail deadlines.

No single national standard specifying separate arrival deadlines for
critical, high, and normal priorities has been verified for India.
Applicable thresholds must come from the relevant State/UT operational
SOP or other authoritative service standard.

How to add a verified threshold
---------------------------------
1. Obtain the official document (State SOP, circular, gazette notification).
2. Confirm the exact measurement definition (e.g., call received → ERU arrival).
3. Add an entry to VERIFIED_STANDARDS below, following the structure shown.
4. Set "verified": True and record the source reference.

Until verified thresholds are configured, response-time compliance will
always be treated as UNKNOWN and will not block a successful classification
on its own — but a successful classification requires BOTH outcome achievement
AND timeliness to be confirmed.
"""

# ---------------------------------------------------------------------------
# Verified response-time standards
# ---------------------------------------------------------------------------
# Each entry maps:
#   priority → {
#       "max_minutes"       : int   — maximum acceptable minutes (ERU arrival),
#       "measurement"       : str   — exact measurement definition,
#       "source"            : str   — authoritative document reference,
#       "verified"          : bool  — True only when confirmed from source,
#   }
#
# Leave this dict empty until a verified standard has been confirmed.
# ---------------------------------------------------------------------------

VERIFIED_STANDARDS: dict[str, dict] = {
    # Example — DO NOT enable without verification:
    #
    # "critical": {
    #     "max_minutes": 10,
    #     "measurement": "call received at ERSS → ERU arrival at incident location",
    #     "source": "<State> Police SOP for ERSS, Section X, dated YYYY-MM-DD",
    #     "verified": True,
    # },
    # "high": {
    #     "max_minutes": 15,
    #     "measurement": "call received at ERSS → ERU arrival at incident location",
    #     "source": "<State> Police SOP for ERSS, Section X, dated YYYY-MM-DD",
    #     "verified": True,
    # },
    # "normal": {
    #     "max_minutes": 20,
    #     "measurement": "call received at ERSS → ERU arrival at incident location",
    #     "source": "<State> Police SOP for ERSS, Section X, dated YYYY-MM-DD",
    #     "verified": True,
    # },
}

# ---------------------------------------------------------------------------
# MHA ERSS 2.0 normalization caps — for reference only, NOT pass/fail limits
# ---------------------------------------------------------------------------

ERSS_NORMALIZATION_CAPS = {
    "call_taker_stage_minutes": 5,
    "dispatcher_stage_minutes": 5,
    "eru_stage_minutes": 50,
    "note": (
        "These caps are used for performance reporting only. "
        "Do not use them as individual-operation pass/fail deadlines. "
        "Source: MHA ERSS 2.0 Guidelines, January 2026."
    ),
}
