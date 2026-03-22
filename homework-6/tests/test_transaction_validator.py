"""Unit tests for Transaction Validator Agent."""
import json
from pathlib import Path

import pytest

from agents.transaction_validator import _dry_run, _mask_account, process_message


def _make_message(data: dict) -> dict:
    return {
        "message_id": "test-001",
        "timestamp": "2026-03-16T10:00:00Z",
        "source_agent": "integrator",
        "target_agent": "transaction_validator",
        "message_type": "transaction",
        "data": data,
    }


def _valid_txn(**overrides) -> dict:
    base = {
        "transaction_id": "TXN001",
        "timestamp": "2026-03-16T09:00:00Z",
        "source_account": "ACC-1001",
        "destination_account": "ACC-2001",
        "amount": "1500.00",
        "currency": "USD",
        "transaction_type": "transfer",
        "description": "Test payment",
        "metadata": {"channel": "online", "country": "US"},
    }
    base.update(overrides)
    return base


class TestValidTransactions:
    def test_valid_usd_transaction_is_validated(self):
        msg = _make_message(_valid_txn())
        result = process_message(msg)
        assert result["data"]["status"] == "validated"

    def test_valid_eur_transaction_is_validated(self):
        msg = _make_message(_valid_txn(currency="EUR"))
        result = process_message(msg)
        assert result["data"]["status"] == "validated"

    def test_valid_gbp_transaction_is_validated(self):
        msg = _make_message(_valid_txn(currency="GBP"))
        result = process_message(msg)
        assert result["data"]["status"] == "validated"

    def test_source_agent_set_to_validator(self):
        msg = _make_message(_valid_txn())
        result = process_message(msg)
        assert result["source_agent"] == "transaction_validator"

    def test_amount_normalized_to_string(self):
        msg = _make_message(_valid_txn(amount="1500.00"))
        result = process_message(msg)
        assert result["data"]["amount"] == "1500.00"


class TestMissingFields:
    @pytest.mark.parametrize("field", [
        "transaction_id", "amount", "currency",
        "source_account", "destination_account", "timestamp",
    ])
    def test_missing_required_field_is_rejected(self, field):
        txn = _valid_txn()
        del txn[field]
        msg = _make_message(txn)
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] == "MISSING_FIELD"


class TestInvalidAmount:
    def test_negative_amount_is_rejected(self):
        msg = _make_message(_valid_txn(amount="-100.00"))
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] == "INVALID_AMOUNT"

    def test_zero_amount_is_rejected(self):
        msg = _make_message(_valid_txn(amount="0"))
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] == "INVALID_AMOUNT"

    def test_non_numeric_amount_is_rejected(self):
        msg = _make_message(_valid_txn(amount="abc"))
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] == "INVALID_AMOUNT"


class TestInvalidCurrency:
    def test_unknown_currency_xyz_is_rejected(self):
        msg = _make_message(_valid_txn(currency="XYZ"))
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] == "INVALID_CURRENCY"

    def test_lowercase_currency_is_normalised_and_validated(self):
        msg = _make_message(_valid_txn(currency="usd"))
        result = process_message(msg)
        assert result["data"]["status"] == "validated"
        assert result["data"]["currency"] == "USD"

    def test_empty_currency_is_rejected(self):
        # empty string fails MISSING_FIELD check (falsy) before reaching currency validation
        msg = _make_message(_valid_txn(currency=""))
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] in ("MISSING_FIELD", "INVALID_CURRENCY")


class TestMaskAccount:
    def test_long_account_masked(self):
        assert _mask_account("ACC-1001") == "****1001"

    def test_short_account_unchanged(self):
        assert _mask_account("1234") == "1234"


class TestDryRun:
    def test_dry_run_prints_results(self, tmp_path, capsys):
        transactions = [
            {
                "transaction_id": "TXN001",
                "timestamp": "2026-03-16T09:00:00Z",
                "source_account": "ACC-1001",
                "destination_account": "ACC-2001",
                "amount": "1500.00",
                "currency": "USD",
                "transaction_type": "transfer",
                "description": "Test",
                "metadata": {"channel": "online", "country": "US"},
            },
            {
                "transaction_id": "TXN002",
                "timestamp": "2026-03-16T09:15:00Z",
                "source_account": "ACC-1002",
                "destination_account": "ACC-3001",
                "amount": "200.00",
                "currency": "XYZ",
                "transaction_type": "transfer",
                "description": "Bad currency",
                "metadata": {"channel": "online", "country": "US"},
            },
        ]
        f = tmp_path / "txns.json"
        f.write_text(json.dumps(transactions))
        _dry_run(f)
        out = capsys.readouterr().out
        assert "TXN001" in out
        assert "validated" in out
        assert "TXN002" in out
        assert "Total" in out


class TestSampleTransactions:
    """Verify the 8 sample transactions produce expected outcomes."""

    def test_txn003_consulting_payment_validated(self):
        # 9999.99 USD — valid (just under 10k)
        msg = _make_message(_valid_txn(
            transaction_id="TXN003",
            amount="9999.99",
            currency="USD",
        ))
        result = process_message(msg)
        assert result["data"]["status"] == "validated"

    def test_txn006_xyz_currency_rejected(self):
        msg = _make_message(_valid_txn(
            transaction_id="TXN006",
            amount="200.00",
            currency="XYZ",
        ))
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] == "INVALID_CURRENCY"

    def test_txn007_negative_amount_rejected(self):
        msg = _make_message(_valid_txn(
            transaction_id="TXN007",
            amount="-100.00",
            currency="GBP",
        ))
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert result["data"]["rejection_reason"] == "INVALID_AMOUNT"
