"""Settlement Processor Agent

Final agent in the pipeline. Settles or holds transactions based on
fraud risk level, then writes the final result to shared/results/.
"""
import json
import logging
from pathlib import Path

AGENT_NAME = "settlement_processor"

RESULTS_DIR = Path(__file__).parent.parent / "shared" / "results"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(AGENT_NAME)


def process_message(message: dict, results_dir: Path = None) -> dict:
    """Settle or hold a transaction based on fraud risk level.

    - fraud_risk_level LOW or MEDIUM → status: "settled"
    - fraud_risk_level HIGH           → status: "held_for_review"
    - status "rejected"               → pass through unchanged

    Writes final result JSON to shared/results/{transaction_id}.json.

    Args:
        message: Message envelope with fraud-scored transaction data.
        results_dir: Override results directory (used in tests).

    Returns:
        Message with final status set.
    """
    if results_dir is None:
        results_dir = RESULTS_DIR

    data = message.get("data", {})
    status = data.get("status")
    transaction_id = data.get("transaction_id", "UNKNOWN")
    risk_level = data.get("fraud_risk_level")

    if status == "rejected":
        final_status = "rejected"
    elif risk_level == "HIGH":
        final_status = "held_for_review"
    elif risk_level in ("LOW", "MEDIUM"):
        final_status = "settled"
    else:
        # validated but no risk score (shouldn't happen in normal flow)
        final_status = "settled"

    message["data"]["status"] = final_status
    message["source_agent"] = AGENT_NAME

    logger.info(
        "agent=%s transaction_id=%s outcome=%s risk_level=%s",
        AGENT_NAME,
        transaction_id,
        final_status,
        risk_level or "N/A",
    )

    # Write final result to shared/results/
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    result_path = results_dir / f"{transaction_id}.json"
    with open(result_path, "w") as f:
        json.dump(message, f, indent=2)

    return message
