# Emergency Response Operation Success Classifier

An AI-powered classifier that evaluates whether an emergency response operation was successful, based on three inputs:

- **Case priority** — `critical`, `high`, or `normal`
- **Response time** — free-text value with unit (e.g. `8 minutes`, `45 seconds`)
- **Officers' comments** — free-text description of what happened during the operation

The classifier returns exactly one of three outcomes:

| `is_success` value | Meaning |
|---|---|
| `true` | Operation was successful |
| `false` | Operation was unsuccessful |
| `"insufficient_info"` | Insufficient information to decide |

---

## How it works

```
User input
    │
    ▼
Input validation          ← Deterministic: rejects invalid priority values
    │
    ▼
Comments analysis         ← Local LLM (Ollama): interprets officers' comments
    │                        Returns: achieved / not_achieved / unknown
    ▼
Response-time evaluation  ← Deterministic: checks against configurable standards
    │                        Returns: timely / not_timely / unknown
    ▼
Decision engine           ← Deterministic: applies fixed decision table
    │
    ▼
{"is_success": true | false | "insufficient_info"}
```

The LLM is used **only** to interpret officers' comments. All other logic is deterministic. Response-time standards are configurable and no thresholds are hardcoded.

---

## Requirements

- Python 3.11 or later
- [Ollama](https://ollama.com/) installed and running locally
- The `erss` custom model (built from the included `Modelfile`)

> **Note on hardware:** The base model is `llama3.2:1b` (1.3 GB). It runs comfortably on 16 GB RAM. A GPU is not required but speeds up inference.

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd emergency-response-classifier
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate.bat     # Windows
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and start Ollama

Follow the instructions at [https://ollama.com/download](https://ollama.com/download).

Then start the Ollama service:

```bash
ollama serve
```

### 5. Pull the base model

```bash
ollama pull llama3.2:1b
```

### 6. Build the custom `erss` model

```bash
ollama create erss -f Modelfile
```

Verify that the model is available:

```bash
ollama list
```

You should see `erss:latest` in the list.

---

## Usage

### Interactive mode

```bash
python main.py
```

Example session:

```text
====================================
  EMERGENCY RESPONSE CLASSIFIER
====================================

Enter case priority (critical/high/normal): critical
Enter response time (include unit if known, otherwise enter unknown): 8 minutes
Enter officers' comments about the operation: The missing person was located and reunited with family.

------------------------------------
  Analysing — please wait...
------------------------------------

====================================
             RESULT
====================================

{
  "is_success": "insufficient_info"
}
```

> `"insufficient_info"` is the expected result when no verified response-time standard is configured for the given priority (see [Configuration](#configuration) below).

### Demo mode (pre-configured scenarios)

Runs five fixed scenarios without requiring keyboard input. Useful for smoke-testing after model changes.

```bash
python demo.py
```

---

## Running tests

All unit tests are LLM-free and run without Ollama:

```bash
pytest tests/ -v
```

Expected output:

```
83 passed in 0.14s
```

---

## Configuration

### Response-time standards

By default, **no response-time standard is configured**. This means timeliness is always `unknown`, which prevents the classifier from returning `true` (a successful classification requires both outcome achievement *and* confirmed timeliness).

To add a verified standard, edit [`src/config/response_time_standards.py`](src/config/response_time_standards.py):

```python
VERIFIED_STANDARDS = {
    "critical": {
        "max_minutes": 10,
        "measurement": "call received at ERSS → ERU arrival at incident location",
        "source": "<State> Police SOP, Section X, dated YYYY-MM-DD",
        "verified": True,
    },
    # Add "high" and "normal" similarly
}
```

> **Important:** Only add entries backed by an authoritative source (State/UT SOP or official circular). Do not invent thresholds.
>
> The MHA ERSS 2.0 Guidelines (January 2026) normalization caps (5 / 5 / 50 minutes) are **not** individual-operation pass/fail deadlines and must not be used as thresholds.

---

## Project structure

```
emergency-response-classifier/
├── main.py                              # Interactive terminal entry point
├── demo.py                              # Pre-configured demo scenarios
├── Modelfile                            # Ollama custom model configuration
├── requirements.txt                     # Python dependencies
│
├── src/
│   ├── classifier.py                    # Public classify() API
│   ├── config/
│   │   └── response_time_standards.py  # Configurable response-time standards
│   ├── validation/
│   │   └── input_validator.py          # Input validation
│   ├── analysis/
│   │   └── comments_analyzer.py        # LLM-based comments analysis
│   ├── evaluation/
│   │   └── response_time_evaluator.py  # Deterministic timeliness evaluation
│   ├── classification/
│   │   └── decision_engine.py          # Decision table logic
│   └── llm/
│       └── llama_client.py             # Ollama API client
│
└── tests/
    ├── test_comments_analyzer.py        # Comments analyzer tests (mocked LLM)
    ├── test_decision_engine.py          # Decision table tests
    ├── test_input_validator.py          # Input validation tests
    ├── test_main_input.py               # Interactive input function tests
    └── test_response_time_evaluator.py  # Response-time evaluator tests
```

---

## Classification logic

### Decision table

| Outcome achievement | Timeliness | `is_success` |
|---|---|---|
| `achieved` | `timely` | `true` |
| `not_achieved` | *(any)* | `false` |
| *(any)* | `not_timely` | `false` |
| `achieved` | `unknown` | `"insufficient_info"` |
| `unknown` | `timely` | `"insufficient_info"` |
| `unknown` | `unknown` | `"insufficient_info"` |

If either dimension is conclusively negative, the result is always `false`, even when the other is unknown.

### Outcome achievement states (from LLM)

| State | When used |
|---|---|
| `achieved` | Comments contain **explicit positive evidence** the objective was completed |
| `not_achieved` | Comments contain **explicit negative evidence** the objective failed |
| `unknown` | Deployment/arrival only, ongoing operations, ambiguous or missing comments |

> Missing evidence of success is **not** evidence of failure.

---

## Known limitations

- **`is_success: true` is currently unreachable** until a verified response-time standard is added to `src/config/response_time_standards.py`.
- The LLM (1B parameter model) may misinterpret complex or multi-sentence comments. Accuracy has not been formally validated on real operational data.
- Response-time measurement definition (what start and end events the clock measures) has not yet been officially established. The classifier preserves the supplied value without assuming units or converting formats.

---

## Reference

- [MHA ERSS 2.0 Guidelines, January 2026](https://mha.gov.in/) — national reference framework for Indian emergency response standards
