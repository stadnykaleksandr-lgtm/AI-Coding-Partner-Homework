"""Fraud Detector Agent

Scores validated transactions for fraud risk based on amount, timing,
and cross-border indicators.
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal

AGENT_NAME = "fraud_detector"

THRESHOLD_HIGH_VALUE = Decimal("10000")
THRESHOLD_VERY_HIGH_VALUE = Decimal("50000")

SCORE_HIGH_VALUE = 3
SCORE_VERY_HIGH_VALUE = 4
SCORE_UNUSUAL_HOUR = 2
SCORE_CROSS_BORDER = 1

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(AGENT_NAME)


def _is_unusual_hour(timestamp_str: str) -> bool:
    """Return True if transaction hour is 2am–5am UTC (unusual hours)."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return 2 <= dt.hour < 5
    except (ValueError, AttributeError):
        return False


def _is_cross_border(data: dict) -> bool:
    """Return True if transaction metadata indicates cross-border."""
    metadata = data.get("metadata", {})
    country = metadata.get("country", "")
    # Treat non-US transactions as cross-border (US is the domestic baseline)
    return country not in ("", "US")


def _compute_score(data: dict) -> int:
    """Compute fraud risk score for a transaction."""
    score = 0
    try:
        amount = Decimal(str(data.get("amount", "0")))
    except Exception:
        amount = Decimal("0")

    if amount > THRESHOLD_HIGH_VALUE:
        score += SCORE_HIGH_VALUE
    if amount > THRESHOLD_VERY_HIGH_VALUE:
        score += SCORE_VERY_HIGH_VALUE

    if _is_unusual_hour(data.get("timestamp", "")):
        score += SCORE_UNUSUAL_HOUR

    if _is_cross_border(data):
        score += SCORE_CROSS_BORDER

    return score


def _score_to_level(score: int) -> str:
    if score <= 2:
        return RISK_LOW
    if score <= 6:
        return RISK_MEDIUM
    return RISK_HIGH


def process_message(message: dict) -> dict:
    """Score a transaction message for fraud risk.

    Passes through rejected messages unchanged. Adds fraud_risk_score
    and fraud_risk_level to validated messages.

    Args:
        message: Message envelope with data containing transaction fields.

    Returns:
        Message with fraud_risk_score and fraud_risk_level added to data.
    """
    data = message.get("data", {})
    status = data.get("status")
    transaction_id = data.get("transaction_id", "UNKNOWN")

    if status != "validated":
        logger.info(
            "agent=%s transaction_id=%s outcome=skipped status=%s",
            AGENT_NAME,
            transaction_id,
            status,
        )
        message["source_agent"] = AGENT_NAME
        return message

    score = _compute_score(data)
    level = _score_to_level(score)

    logger.info(
        "agent=%s transaction_id=%s outcome=scored score=%d level=%s",
        AGENT_NAME,
        transaction_id,
        score,
        level,
    )

    message["data"]["fraud_risk_score"] = score
    message["data"]["fraud_risk_level"] = level
    message["source_agent"] = AGENT_NAME
    return message
