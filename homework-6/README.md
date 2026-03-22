# AI-Powered Multi-Agent Banking Pipeline

**Created by Oleksiy Stadnyk**

A Python pipeline that validates, scores for fraud risk, and settles banking transactions using three cooperating agents communicating via file-based JSON message passing.

This project was built as part of Homework 6 — a capstone demonstrating AI-assisted code generation using Claude Code, custom skills, MCP servers, and automated coverage gates.

---

## What it does

The pipeline reads raw transactions from `sample-transactions.json`, passes each through three agents in sequence, and writes a final result file to `shared/results/`. Each agent performs one responsibility — validation, fraud scoring, or settlement — and hands off to the next via a standard JSON message envelope.

Transactions that fail validation are rejected immediately. Valid transactions are scored for fraud risk; high-risk transactions are held for review while low/medium-risk ones are settled. The integrator prints a summary report at the end.

---

## Agent Responsibilities

| Agent | File | Responsibility |
|---|---|---|
| Transaction Validator | `agents/transaction_validator.py` | Checks required fields, validates amount (positive Decimal), validates ISO 4217 currency |
| Fraud Detector | `agents/fraud_detector.py` | Scores transactions on amount, time of day, and cross-border indicators; assigns LOW/MEDIUM/HIGH |
| Settlement Processor | `agents/settlement_processor.py` | Settles LOW/MEDIUM risk transactions; holds HIGH risk; writes final result to `shared/results/` |
| Integrator | `integrator.py` | Orchestrates the pipeline, loads transactions, prints summary report |

---

## Pipeline Architecture

```
sample-transactions.json
         │
         ▼
    integrator.py
    (wrap in message envelope)
         │
         ▼
┌─────────────────────────┐
│  Transaction Validator  │  ── validates fields, amount, currency
└─────────────────────────┘
         │
         ▼  (validated / rejected)
┌─────────────────────────┐
│     Fraud Detector      │  ── scores risk: amount, hour, cross-border
└─────────────────────────┘
         │
         ▼  (fraud_risk_level: LOW / MEDIUM / HIGH)
┌─────────────────────────┐
│  Settlement Processor   │  ── settled / held_for_review / rejected
└─────────────────────────┘
         │
         ▼
   shared/results/
   {transaction_id}.json
         │
         ▼
   Pipeline Summary Report
   (printed to stdout)
```

---

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.10+ |
| Monetary arithmetic | `decimal.Decimal` (never `float`) |
| Currency validation | ISO 4217 whitelist (USD, EUR, GBP, JPY, CAD, AUD, CHF) |
| Message transport | File-based JSON (`shared/input/`, `processing/`, `output/`, `results/`) |
| MCP server | `fastmcp` |
| Testing | `pytest` + `pytest-cov` |
| Coverage gate | Pre-push hook in `.claude/settings.json` (blocks push if < 80%) |
| AI assistant | Claude Code (claude-sonnet-4-6) |

---

## Fraud Scoring Rules

| Trigger | Points |
|---|---|
| amount > $10,000 | +3 |
| amount > $50,000 | +4 (cumulative +7) |
| Transaction hour 2–5am UTC | +2 |
| Cross-border (non-US country) | +1 |

| Score | Risk Level | Settlement |
|---|---|---|
| 0–2 | LOW | settled |
| 3–6 | MEDIUM | settled |
| 7–10 | HIGH | held_for_review |

---

## Sample Transaction Outcomes

| ID | Amount | Currency | Expected Outcome |
|---|---|---|---|
| TXN001 | $1,500 | USD | settled (LOW risk) |
| TXN002 | $25,000 | USD | settled (MEDIUM risk) |
| TXN003 | $9,999.99 | USD | settled (LOW risk) |
| TXN004 | €500 | EUR | settled (MEDIUM — 2:47am + cross-border) |
| TXN005 | $75,000 | USD | held_for_review (HIGH risk) |
| TXN006 | $200 | XYZ | rejected (INVALID_CURRENCY) |
| TXN007 | -$100 | GBP | rejected (INVALID_AMOUNT) |
| TXN008 | $3,200 | USD | settled (LOW risk) |

---

## Project Structure

```
homework-6/
├── agents/
│   ├── transaction_validator.py
│   ├── fraud_detector.py
│   └── settlement_processor.py
├── tests/
│   ├── test_transaction_validator.py
│   ├── test_fraud_detector.py
│   ├── test_settlement_processor.py
│   └── test_integration.py
├── shared/
│   ├── input/
│   ├── processing/
│   ├── output/
│   └── results/
├── mcp/
│   └── server.py
├── scripts/
│   └── check-coverage.sh
├── docs/
│   └── screenshots/
├── .claude/
│   ├── commands/
│   │   ├── write-spec.md
│   │   ├── run-pipeline.md
│   │   └── validate-transactions.md
│   └── settings.json
├── integrator.py
├── specification.md
├── agents.md
├── research-notes.md
├── mcp.json
├── PLAN.md
└── HOWTORUN.md
```
