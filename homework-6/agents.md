# Agents

This file describes the AI agents (meta-agents) and pipeline agents in this project.

---

## Meta-Agents (build the system)

### Agent 1 — Specification Agent
**Role**: Produces the technical specification for the transaction processing pipeline.
**Skill**: `/write-spec` — invokes `.claude/commands/write-spec.md` to generate `specification.md` from the template.
**Output**: `specification.md`, `agents.md`

### Agent 2 — Code Generation Agent
**Role**: Implements the multi-agent pipeline from the specification.
**MCP**: Uses `context7` during code generation to look up Python `decimal` module and `fastmcp` library docs.
**Output**: `integrator.py`, `agents/transaction_validator.py`, `agents/fraud_detector.py`, `agents/settlement_processor.py`, `research-notes.md`

### Agent 3 — Unit Test Agent
**Role**: Creates the test suite and enforces coverage.
**Hook**: Pre-push hook in `.claude/settings.json` runs `pytest --cov` and blocks push if coverage < 80%.
**Skills**: `/run-pipeline`, `/validate-transactions`
**Output**: `tests/`, `.claude/commands/run-pipeline.md`, `.claude/commands/validate-transactions.md`

### Agent 4 — Documentation Agent
**Role**: Generates README, HOWTORUN, and project docs.
**Requirement**: README must include author name.
**Output**: `README.md`, `HOWTORUN.md`

---

## Pipeline Agents (process transactions)

### Transaction Validator (`agents/transaction_validator.py`)
**Input**: Raw transaction message from `sample-transactions.json`
**Process**:
- Validates required fields: `transaction_id`, `amount`, `currency`, `source_account`, `destination_account`, `timestamp`
- Validates `amount` is a positive `decimal.Decimal`
- Validates `currency` against ISO 4217 whitelist (USD, EUR, GBP, JPY, CAD, AUD, CHF)
**Output**: Message with `status: "validated"` or `"rejected"` + `rejection_reason`
**Rejection reasons**: `MISSING_FIELD`, `INVALID_AMOUNT`, `INVALID_CURRENCY`

### Fraud Detector (`agents/fraud_detector.py`)
**Input**: Validated transaction message
**Process**:
- Passes through `status: "rejected"` messages unchanged
- Scores validated transactions:
  - amount > $10,000 → +3 pts
  - amount > $50,000 → +4 more pts
  - transaction hour 2–5am UTC → +2 pts
  - cross-border (country in metadata) → +1 pt
- Risk levels: LOW (0–2), MEDIUM (3–6), HIGH (7–10)
**Output**: Message with `fraud_risk_score` (int) and `fraud_risk_level` ("LOW"/"MEDIUM"/"HIGH") added

### Settlement Processor (`agents/settlement_processor.py`)
**Input**: Fraud-scored transaction message
**Process**:
- `fraud_risk_level` LOW or MEDIUM → `status: "settled"`
- `fraud_risk_level` HIGH → `status: "held_for_review"`
- `status: "rejected"` → pass through unchanged
**Output**: Final result JSON written to `shared/results/{transaction_id}.json`

---

## Message Flow

```
sample-transactions.json
        |
        v
   integrator.py  ──── loads transactions, wraps in message envelope, drops to shared/input/
        |
        v
Transaction Validator ──── reads from shared/input/, writes to shared/output/
        |
        v
Fraud Detector ──── reads from shared/output/, writes to shared/output/
        |
        v
Settlement Processor ──── reads from shared/output/, writes final to shared/results/
        |
        v
   Pipeline Summary  ──── printed to stdout by integrator.py
```

---

## Message Envelope Format

```json
{
  "message_id": "<uuid4>",
  "timestamp": "<ISO 8601>",
  "source_agent": "<agent_name>",
  "target_agent": "<agent_name>",
  "message_type": "transaction",
  "data": {
    "transaction_id": "TXN001",
    "amount": "1500.00",
    "currency": "USD",
    "source_account": "ACC-1001",
    "destination_account": "ACC-2001",
    "status": "validated"
  }
}
```
