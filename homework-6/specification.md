# Specification: Multi-Agent Banking Transaction Pipeline

## 1. High-Level Objective

Build a 3-agent Python pipeline that validates, scores for fraud risk, and settles banking transactions using file-based JSON message passing through a shared directory structure.

---

## 2. Mid-Level Objectives

- Transactions with missing required fields or invalid currency codes are rejected with a specific `reason` field (e.g., `"INVALID_CURRENCY"`, `"MISSING_FIELD"`)
- Transactions above $10,000 are assigned `fraud_risk_level: "HIGH"` or `"MEDIUM"` by the Fraud Detector based on cumulative scoring
- Transactions with `fraud_risk_level: "HIGH"` are held for review (`status: "held_for_review"`); LOW/MEDIUM are settled (`status: "settled"`)
- The pipeline processes all 8 sample transactions and writes 8 result files to `shared/results/`
- All agent operations write to an audit log with ISO 8601 timestamps, masked account numbers, and outcome within each processing step

---

## 3. Implementation Notes

- **Monetary values**: use `decimal.Decimal` exclusively — never `float`
- **Currency validation**: ISO 4217 whitelist — USD, EUR, GBP, JPY, CAD, AUD, CHF; reject anything else (e.g., XYZ)
- **Logging**: audit trail per agent — fields: `timestamp`, `agent`, `transaction_id`, `outcome`
- **PII**: mask account numbers in all log output — show only last 4 characters (e.g., `****1001`)
- **Message passing**: JSON files flow through `shared/input/` → `shared/processing/` → `shared/output/` → `shared/results/`
- **Message envelope**:
  ```json
  {
    "message_id": "<uuid4>",
    "timestamp": "<ISO 8601>",
    "source_agent": "<agent_name>",
    "target_agent": "<agent_name>",
    "message_type": "transaction",
    "data": { ... }
  }
  ```
- **Error handling**: any unhandled exception per transaction must be caught, logged, and written as `status: "error"` to results — pipeline must not halt on a single failure

---

## 4. Context

- **Beginning state**: `sample-transactions.json` exists with 8 raw transaction records. No agents exist. No `shared/` directories exist.
- **Ending state**: All 8 transactions processed. Results in `shared/results/{transaction_id}.json`. A pipeline summary report printed to stdout showing counts of validated/rejected/settled/held. Test coverage ≥ 90%. `README.md` and `HOWTORUN.md` complete.

---

## 5. Low-Level Tasks

### Task: Transaction Validator

**Prompt**:
```
Context: Python pipeline project. shared/ directories exist (input/, processing/, output/, results/).
Use decimal.Decimal for all monetary values. No float. Account numbers are PII — mask in logs.

Task: Create agents/transaction_validator.py with a process_message(message: dict) -> dict function.

Rules:
- Check required fields: transaction_id, amount, currency, source_account, destination_account, timestamp
- Validate amount is a positive decimal.Decimal (convert from string)
- Validate currency against ISO 4217 whitelist: USD, EUR, GBP, JPY, CAD, AUD, CHF
- Return message dict with data.status set to "validated" or "rejected"
- If rejected, add data.rejection_reason (e.g. "MISSING_FIELD", "INVALID_AMOUNT", "INVALID_CURRENCY")
- Write audit log line: timestamp, agent=transaction_validator, transaction_id, outcome
- Support --dry-run CLI flag: reads sample-transactions.json, validates each, prints table, does not write files

Output: agents/transaction_validator.py
```

**File to CREATE**: `agents/transaction_validator.py`
**Function to CREATE**: `process_message(message: dict) -> dict`
**Details**:
- Check required fields: `transaction_id`, `amount`, `currency`, `source_account`, `destination_account`, `timestamp`
- Validate `amount` is a positive `decimal.Decimal`
- Validate `currency` against ISO 4217 whitelist (USD, EUR, GBP, JPY, CAD, AUD, CHF)
- Return message with `data.status: "validated"` or `"rejected"` + `data.rejection_reason`
- Support `--dry-run` CLI flag for use by the `validate-transactions` skill

---

### Task: Fraud Detector

**Prompt**:
```
Context: Python pipeline. Receives validated transaction messages from transaction_validator.
Use decimal.Decimal for amount comparisons. No float.

Task: Create agents/fraud_detector.py with a process_message(message: dict) -> dict function.

Rules:
- Only process messages where data.status == "validated"; pass through others unchanged
- Fraud scoring (cumulative):
    amount > 10000  → +3 pts
    amount > 50000  → +4 more pts (total +7 if both apply)
    hour 2–4am UTC  → +2 pts
    source_account country != destination country (cross-border) → +1 pt
- Risk levels: LOW (0–2), MEDIUM (3–6), HIGH (7–10)
- Add data.fraud_risk_score (int) and data.fraud_risk_level ("LOW"/"MEDIUM"/"HIGH") to message
- Write audit log line: timestamp, agent=fraud_detector, transaction_id, score, level

Output: agents/fraud_detector.py
```

**File to CREATE**: `agents/fraud_detector.py`
**Function to CREATE**: `process_message(message: dict) -> dict`
**Details**:
- Only process `status: "validated"` messages; pass others through unchanged
- Score: amount > $10,000 (+3), amount > $50,000 (+4 more), hour 2–5am UTC (+2), cross-border (+1)
- Risk levels: LOW (0–2), MEDIUM (3–6), HIGH (7–10)
- Add `data.fraud_risk_score` (int) and `data.fraud_risk_level` to output

---

### Task: Settlement Processor

**Prompt**:
```
Context: Python pipeline. Receives fraud-scored transaction messages. Final agent in the pipeline.
Writes final result files to shared/results/.

Task: Create agents/settlement_processor.py with a process_message(message: dict) -> dict function.

Rules:
- fraud_risk_level LOW or MEDIUM → set data.status = "settled"
- fraud_risk_level HIGH → set data.status = "held_for_review"
- data.status "rejected" → pass through unchanged (status stays "rejected")
- Write final result to shared/results/{transaction_id}.json
- Write audit log: timestamp, agent=settlement_processor, transaction_id, final_status

Output: agents/settlement_processor.py
```

**File to CREATE**: `agents/settlement_processor.py`
**Function to CREATE**: `process_message(message: dict) -> dict`
**Details**:
- `fraud_risk_level` LOW or MEDIUM → `status: "settled"`
- `fraud_risk_level` HIGH → `status: "held_for_review"`
- `status: "rejected"` → pass through unchanged
- Write final result JSON to `shared/results/{transaction_id}.json`
