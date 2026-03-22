"""Integrator / Orchestrator

Loads transactions from sample-transactions.json, wraps each in a message
envelope, passes them through the 3-agent pipeline in sequence, and prints
a summary report.

Pipeline:
  Transaction Validator → Fraud Detector → Settlement Processor
"""
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agents.fraud_detector import process_message as fraud_detect
from agents.settlement_processor import process_message as settle
from agents.transaction_validator import process_message as validate

BASE_DIR = Path(__file__).parent
SHARED_DIR = BASE_DIR / "shared"
INPUT_DIR = SHARED_DIR / "input"
PROCESSING_DIR = SHARED_DIR / "processing"
OUTPUT_DIR = SHARED_DIR / "output"
RESULTS_DIR = SHARED_DIR / "results"
TRANSACTIONS_FILE = BASE_DIR / "sample-transactions.json"


def setup_directories() -> None:
    """Create shared directories, clearing output and results from prior runs."""
    for d in [INPUT_DIR, PROCESSING_DIR, OUTPUT_DIR, RESULTS_DIR]:
        if d in (OUTPUT_DIR, RESULTS_DIR):
            shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)


def make_message(transaction: dict) -> dict:
    """Wrap a raw transaction in the standard message envelope."""
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_agent": "integrator",
        "target_agent": "transaction_validator",
        "message_type": "transaction",
        "data": dict(transaction),
    }


def run_pipeline(transactions_file: Path = TRANSACTIONS_FILE, results_dir: Path = RESULTS_DIR) -> list[dict]:
    """Run the full pipeline and return list of final result messages."""
    with open(transactions_file) as f:
        transactions = json.load(f)

    results = []
    for txn in transactions:
        message = make_message(txn)
        try:
            message = validate(message)
            message = fraud_detect(message)
            message = settle(message, results_dir=results_dir)
        except Exception as e:
            txn_id = txn.get("transaction_id", "UNKNOWN")
            print(f"[ERROR] transaction_id={txn_id} error={e}")
            message["data"]["status"] = "error"
            message["data"]["error"] = str(e)
        results.append(message)

    return results


def print_summary(results: list[dict]) -> None:
    """Print a formatted pipeline summary report."""
    counts = {"validated_total": 0, "rejected": 0, "settled": 0, "held_for_review": 0, "error": 0}

    for msg in results:
        status = msg["data"].get("status", "unknown")
        if status in counts:
            counts[status] += 1
        if status in ("settled", "held_for_review"):
            counts["validated_total"] += 1

    total = len(results)
    print("\n" + "=" * 55)
    print("  PIPELINE SUMMARY REPORT")
    print("=" * 55)
    print(f"  Total transactions processed : {total}")
    print(f"  Settled                      : {counts['settled']}")
    print(f"  Held for review (HIGH risk)  : {counts['held_for_review']}")
    print(f"  Rejected                     : {counts['rejected']}")
    print(f"  Errors                       : {counts['error']}")
    print("=" * 55)

    print("\n  Transaction Detail:")
    print(f"  {'ID':<10} {'Status':<20} {'Risk':<8} {'Reject Reason'}")
    print("  " + "-" * 55)
    for msg in results:
        d = msg["data"]
        print(
            f"  {d.get('transaction_id', ''):<10} "
            f"{d.get('status', ''):<20} "
            f"{d.get('fraud_risk_level', 'N/A'):<8} "
            f"{d.get('rejection_reason', '')}"
        )
    print()


if __name__ == "__main__":
    print("Setting up shared directories...")
    setup_directories()

    print(f"Loading transactions from {TRANSACTIONS_FILE}...")
    results = run_pipeline()

    print_summary(results)
    print(f"Results written to {RESULTS_DIR}/")
