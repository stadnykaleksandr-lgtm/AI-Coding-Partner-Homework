Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that `sample-transactions.json` exists in the current directory. If it doesn't, stop and report the error.
2. Clear the `shared/output/` and `shared/results/` directories (leave `shared/input/` and `shared/processing/` intact).
3. Run the pipeline: `python integrator.py`
4. Show a summary of results from `shared/results/` — list each result file and its final status, fraud_risk_level, and rejection_reason if applicable.
5. Report any transactions that were rejected and why, and any that were held for review.
