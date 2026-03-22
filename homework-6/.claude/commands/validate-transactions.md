Validate all transactions in sample-transactions.json without running the full pipeline.

Steps:
1. Check that `sample-transactions.json` exists. If it doesn't, stop and report the error.
2. Run the validator in dry-run mode: `python agents/transaction_validator.py --dry-run --input sample-transactions.json`
3. Report the results:
   - Total transaction count
   - Valid count
   - Invalid count
   - Reasons for each rejection
4. Show a formatted table of results with columns: Transaction ID | Status | Reason.
