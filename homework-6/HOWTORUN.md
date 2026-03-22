# How to Run

## Prerequisites

- Python 3.10+
- `pip3 install pytest pytest-cov fastmcp`

---

## 1. Setup

Clone the repo and navigate to the project directory:

```bash
cd homework-6
```

Install dependencies:

```bash
pip3 install pytest pytest-cov fastmcp
```

---

## 2. Run the pipeline

```bash
python3 integrator.py
```

This will:
1. Create `shared/` directories (clearing output/results from prior runs)
2. Load all 8 transactions from `sample-transactions.json`
3. Run each through: Validator → Fraud Detector → Settlement Processor
4. Write results to `shared/results/{transaction_id}.json`
5. Print a summary report

Expected output:
```
Setting up shared directories...
Loading transactions from sample-transactions.json...

=======================================================
  PIPELINE SUMMARY REPORT
=======================================================
  Total transactions processed : 8
  Settled                      : 5
  Held for review (HIGH risk)  : 1
  Rejected                     : 2
  Errors                       : 0
=======================================================
...
```

---

## 3. Validate transactions only (dry run)

```bash
python3 agents/transaction_validator.py --dry-run
```

Or with a custom file:

```bash
python3 agents/transaction_validator.py --dry-run --input sample-transactions.json
```

---

## 4. Run tests

```bash
python3 -m pytest tests/ -v
```

With coverage report:

```bash
python3 -m pytest tests/ --cov=agents --cov-report=term-missing
```

---

## 5. Run MCP server (pipeline-status)

```bash
python3 mcp/server.py
```

The server exposes:
- Tool `get_transaction_status(transaction_id)` — query a single transaction result
- Tool `list_pipeline_results()` — summary of all results
- Resource `pipeline://summary` — text summary of latest run

---

## 6. Use Claude Code skills

With Claude Code open in this directory:

```
/run-pipeline
```
Runs the full pipeline end-to-end.

```
/validate-transactions
```
Validates transactions in dry-run mode without processing them.

---

## 7. Inspect results

After running the pipeline, results are in `shared/results/`:

```bash
ls shared/results/
# TXN001.json  TXN002.json  TXN003.json  ...

cat shared/results/TXN001.json
```

Each file contains the full message envelope with final `status`, `fraud_risk_level`, and any `rejection_reason`.
