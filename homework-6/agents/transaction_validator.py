"""Transaction Validator Agent

Validates raw transaction messages for required fields, valid amounts,
and ISO 4217 currency codes.
"""
import argparse
import json
import logging
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

AGENT_NAME = "transaction_validator"

ISO_4217_WHITELIST = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"}

REQUIRED_FIELDS = [
    "transaction_id",
    "amount",
    "currency",
    "source_account",
    "destination_account",
    "timestamp",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger(AGENT_NAME)


def _mask_account(account: str) -> str:
    """Mask account number, showing only last 4 characters."""
    if len(account) <= 4:
        return account
    return "*" * (len(account) - 4) + account[-4:]


def process_message(message: dict) -> dict:
    """Validate a transaction message.

    Args:
        message: Message envelope with 'data' containing raw transaction fields.

    Returns:
        Message with data.status set to 'validated' or 'rejected',
        and data.rejection_reason set if rejected.
    """
    data = message.get("data", {})
    transaction_id = data.get("transaction_id", "UNKNOWN")

    # Check required fields
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            reason = "MISSING_FIELD"
            logger.info(
                "agent=%s transaction_id=%s outcome=rejected reason=%s missing_field=%s",
                AGENT_NAME,
                transaction_id,
                reason,
                field,
            )
            message["data"]["status"] = "rejected"
            message["data"]["rejection_reason"] = reason
            message["data"]["rejection_detail"] = f"Missing required field: {field}"
            message["source_agent"] = AGENT_NAME
            return message

    # Validate amount
    try:
        amount = Decimal(str(data["amount"]))
        if amount <= 0:
            raise ValueError("Amount must be positive")
        message["data"]["amount"] = str(amount)
    except (InvalidOperation, ValueError):
        reason = "INVALID_AMOUNT"
        logger.info(
            "agent=%s transaction_id=%s outcome=rejected reason=%s account=%s",
            AGENT_NAME,
            transaction_id,
            reason,
            _mask_account(data.get("source_account", "")),
        )
        message["data"]["status"] = "rejected"
        message["data"]["rejection_reason"] = reason
        message["data"]["rejection_detail"] = f"Invalid amount: {data.get('amount')}"
        message["source_agent"] = AGENT_NAME
        return message

    # Validate currency
    currency = str(data.get("currency", "")).upper()
    if currency not in ISO_4217_WHITELIST:
        reason = "INVALID_CURRENCY"
        logger.info(
            "agent=%s transaction_id=%s outcome=rejected reason=%s currency=%s",
            AGENT_NAME,
            transaction_id,
            reason,
            currency,
        )
        message["data"]["status"] = "rejected"
        message["data"]["rejection_reason"] = reason
        message["data"]["rejection_detail"] = f"Unsupported currency: {currency}"
        message["source_agent"] = AGENT_NAME
        return message

    # All checks passed
    logger.info(
        "agent=%s transaction_id=%s outcome=validated amount=%s currency=%s account=%s",
        AGENT_NAME,
        transaction_id,
        str(amount),
        currency,
        _mask_account(data.get("source_account", "")),
    )
    message["data"]["status"] = "validated"
    message["data"]["currency"] = currency
    message["source_agent"] = AGENT_NAME
    return message


def _dry_run(transactions_path: Path) -> None:
    """Validate all transactions and print a results table without writing files."""
    with open(transactions_path) as f:
        transactions = json.load(f)

    results = []
    for txn in transactions:
        message = {
            "source_agent": "dry_run",
            "target_agent": AGENT_NAME,
            "data": dict(txn),
        }
        result = process_message(message)
        data = result["data"]
        results.append(
            {
                "transaction_id": data.get("transaction_id"),
                "status": data.get("status"),
                "reason": data.get("rejection_reason", ""),
            }
        )

    valid = sum(1 for r in results if r["status"] == "validated")
    invalid = sum(1 for r in results if r["status"] == "rejected")

    print(f"\nValidation results for {transactions_path}")
    print(f"Total: {len(results)} | Valid: {valid} | Invalid: {invalid}\n")
    print(f"{'Transaction ID':<15} {'Status':<12} {'Reason'}")
    print("-" * 45)
    for r in results:
        print(f"{r['transaction_id']:<15} {r['status']:<12} {r['reason']}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transaction Validator Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate transactions without writing output files",
    )
    parser.add_argument(
        "--input",
        default="sample-transactions.json",
        help="Path to transactions JSON file (used with --dry-run)",
    )
    args = parser.parse_args()

    if args.dry_run:
        _dry_run(Path(args.input))
    else:
        print("Run via integrator.py or use --dry-run for standalone validation.")
        sys.exit(0)
