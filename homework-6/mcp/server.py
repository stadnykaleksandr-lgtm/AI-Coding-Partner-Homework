"""FastMCP Server — Pipeline Status

Exposes tools and resources for querying the state of the transaction pipeline.

Tools:
  - get_transaction_status(transaction_id) — returns status of a processed transaction
  - list_pipeline_results()               — summary of all processed transactions

Resources:
  - pipeline://summary                    — latest pipeline run summary as text
"""
import json
from pathlib import Path

from fastmcp import FastMCP

RESULTS_DIR = Path(__file__).parent.parent / "shared" / "results"

mcp = FastMCP("pipeline-status")


def _load_result(transaction_id: str) -> dict | None:
    """Load a result file by transaction ID."""
    path = RESULTS_DIR / f"{transaction_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _all_results() -> list[dict]:
    """Load all result files from shared/results/."""
    results = []
    if not RESULTS_DIR.exists():
        return results
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            with open(path) as f:
                results.append(json.load(f))
        except Exception:
            pass
    return results


@mcp.tool()
def get_transaction_status(transaction_id: str) -> dict:
    """Get the current status of a processed transaction.

    Args:
        transaction_id: The transaction ID (e.g. "TXN001").

    Returns:
        Dict with transaction_id, status, fraud_risk_level, rejection_reason,
        or an error message if the transaction is not found.
    """
    result = _load_result(transaction_id)
    if result is None:
        return {"error": f"Transaction {transaction_id} not found in shared/results/"}

    data = result.get("data", {})
    return {
        "transaction_id": data.get("transaction_id"),
        "status": data.get("status"),
        "fraud_risk_level": data.get("fraud_risk_level"),
        "fraud_risk_score": data.get("fraud_risk_score"),
        "rejection_reason": data.get("rejection_reason"),
        "rejection_detail": data.get("rejection_detail"),
        "amount": data.get("amount"),
        "currency": data.get("currency"),
    }


@mcp.tool()
def list_pipeline_results() -> dict:
    """Return a summary of all processed transactions.

    Returns:
        Dict with total count, per-status counts, and list of transaction summaries.
    """
    results = _all_results()

    summaries = []
    counts: dict[str, int] = {}
    for msg in results:
        data = msg.get("data", {})
        status = data.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
        summaries.append(
            {
                "transaction_id": data.get("transaction_id"),
                "status": status,
                "fraud_risk_level": data.get("fraud_risk_level"),
                "rejection_reason": data.get("rejection_reason"),
                "amount": data.get("amount"),
                "currency": data.get("currency"),
            }
        )

    return {
        "total": len(results),
        "counts": counts,
        "transactions": summaries,
    }


@mcp.resource("pipeline://summary")
def pipeline_summary() -> str:
    """Return the latest pipeline run summary as plain text."""
    results = _all_results()
    if not results:
        return "No pipeline results found. Run: python integrator.py"

    counts: dict[str, int] = {}
    for msg in results:
        status = msg.get("data", {}).get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1

    lines = [
        "=== Pipeline Run Summary ===",
        f"Total transactions: {len(results)}",
    ]
    for status, count in sorted(counts.items()):
        lines.append(f"  {status}: {count}")

    lines.append("")
    lines.append("Transaction Detail:")
    lines.append(f"{'ID':<10} {'Status':<20} {'Risk':<8} {'Reason'}")
    lines.append("-" * 55)
    for msg in results:
        d = msg.get("data", {})
        lines.append(
            f"{d.get('transaction_id', ''):<10} "
            f"{d.get('status', ''):<20} "
            f"{d.get('fraud_risk_level', 'N/A'):<8} "
            f"{d.get('rejection_reason', '')}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
