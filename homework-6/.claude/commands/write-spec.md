Generate a complete technical specification for the multi-agent banking transaction pipeline using the template structure below.

Read `specification-TEMPLATE-hint.md` and `sample-transactions.json` first to understand the input data and template format.

Then produce `specification.md` with the following five sections:

## 1. High-Level Objective
One sentence describing the full pipeline.

## 2. Mid-Level Objectives
Four to five concrete, testable requirements. Each must be something a test could verify.
Examples:
- Transactions with invalid currency codes are rejected with reason "INVALID_CURRENCY"
- Transactions above $10,000 receive fraud_risk_level "HIGH" from the Fraud Detector
- All agent operations write to the audit log with ISO 8601 timestamps
- The pipeline processes all 8 sample transactions and writes results to shared/results/

## 3. Implementation Notes
- Monetary values: use `decimal.Decimal` — never `float`
- Currency validation: ISO 4217 whitelist (USD, EUR, GBP, JPY, CAD, AUD, CHF minimum)
- Logging: audit trail per agent — timestamp, agent name, transaction_id, outcome
- PII: mask account numbers in all log output (show only last 4 chars)
- File-based message passing through shared/input/, shared/processing/, shared/output/, shared/results/
- Standard message envelope: message_id (uuid4), timestamp, source_agent, target_agent, message_type, data

## 4. Context
- Beginning state: `sample-transactions.json` with 8 raw transaction records, no agents, no shared/ directories
- Ending state: all 8 transactions processed, results in `shared/results/`, pipeline summary printed, test coverage >= 90%

## 5. Low-Level Tasks
One entry per agent in this exact format:

### Task: Transaction Validator
**Prompt**: "[full prompt you will give Claude Code]"
**File to CREATE**: `agents/transaction_validator.py`
**Function to CREATE**: `process_message(message: dict) -> dict`
**Details**:
- Check required fields: transaction_id, amount, currency, source_account, destination_account, timestamp
- Validate amount is a positive decimal.Decimal
- Validate currency against ISO 4217 whitelist
- Return message with status "validated" or "rejected" + reason field
- Support --dry-run CLI flag for use by the validate-transactions skill

### Task: Fraud Detector
**Prompt**: "[full prompt you will give Claude Code]"
**File to CREATE**: `agents/fraud_detector.py`
**Function to CREATE**: `process_message(message: dict) -> dict`
**Details**:
- Only process messages with status "validated"
- Score: amount > $10,000 (+3 pts), amount > $50,000 (+4 more pts), hour 2–5am UTC (+2 pts), cross-border (+1 pt)
- Risk levels: LOW (0–2), MEDIUM (3–6), HIGH (7–10)
- Return message with fraud_risk_score and fraud_risk_level added

### Task: Settlement Processor
**Prompt**: "[full prompt you will give Claude Code]"
**File to CREATE**: `agents/settlement_processor.py`
**Function to CREATE**: `process_message(message: dict) -> dict`
**Details**:
- Settle transactions with fraud_risk_level LOW or MEDIUM → status "settled"
- Hold transactions with fraud_risk_level HIGH → status "held_for_review"
- Rejected transactions pass through with status "rejected"
- Write final result JSON to shared/results/{transaction_id}.json

Write the complete `specification.md` file now.
