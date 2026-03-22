"""Unit tests for Fraud Detector Agent."""
import pytest
from agents.fraud_detector import (
    _compute_score,
    _is_cross_border,
    _is_unusual_hour,
    _score_to_level,
    process_message,
)


def _make_message(data: dict) -> dict:
    return {
        "message_id": "test-002",
        "timestamp": "2026-03-16T10:00:00Z",
        "source_agent": "transaction_validator",
        "target_agent": "fraud_detector",
        "message_type": "transaction",
        "data": data,
    }


def _validated_txn(**overrides) -> dict:
    base = {
        "transaction_id": "TXN001",
        "timestamp": "2026-03-16T09:00:00Z",
        "source_account": "ACC-1001",
        "destination_account": "ACC-2001",
        "amount": "1500.00",
        "currency": "USD",
        "status": "validated",
        "metadata": {"channel": "online", "country": "US"},
    }
    base.update(overrides)
    return base


class TestScoreHelpers:
    def test_unusual_hour_2am(self):
        assert _is_unusual_hour("2026-03-16T02:47:00Z") is True

    def test_unusual_hour_3am(self):
        assert _is_unusual_hour("2026-03-16T03:00:00Z") is True

    def test_unusual_hour_4am(self):
        assert _is_unusual_hour("2026-03-16T04:59:00Z") is True

    def test_normal_hour_9am(self):
        assert _is_unusual_hour("2026-03-16T09:00:00Z") is False

    def test_normal_hour_5am_not_unusual(self):
        # 5am is boundary — 2 <= h < 5, so 5 is NOT unusual
        assert _is_unusual_hour("2026-03-16T05:00:00Z") is False

    def test_cross_border_germany(self):
        assert _is_cross_border({"metadata": {"country": "DE"}}) is True

    def test_cross_border_gb(self):
        assert _is_cross_border({"metadata": {"country": "GB"}}) is True

    def test_domestic_us(self):
        assert _is_cross_border({"metadata": {"country": "US"}}) is False

    def test_no_metadata(self):
        assert _is_cross_border({}) is False


class TestScoreLevels:
    def test_score_0_is_low(self):
        assert _score_to_level(0) == "LOW"

    def test_score_2_is_low(self):
        assert _score_to_level(2) == "LOW"

    def test_score_3_is_medium(self):
        assert _score_to_level(3) == "MEDIUM"

    def test_score_6_is_medium(self):
        assert _score_to_level(6) == "MEDIUM"

    def test_score_7_is_high(self):
        assert _score_to_level(7) == "HIGH"

    def test_score_10_is_high(self):
        assert _score_to_level(10) == "HIGH"


class TestComputeScore:
    def test_low_value_domestic_normal_hour(self):
        data = _validated_txn(amount="1500.00", timestamp="2026-03-16T09:00:00Z")
        assert _compute_score(data) == 0

    def test_high_value_over_10k(self):
        data = _validated_txn(amount="25000.00", timestamp="2026-03-16T09:00:00Z")
        assert _compute_score(data) == 3

    def test_very_high_value_over_50k(self):
        data = _validated_txn(amount="75000.00", timestamp="2026-03-16T09:00:00Z")
        assert _compute_score(data) == 7  # 3 + 4

    def test_unusual_hour_adds_2(self):
        data = _validated_txn(amount="500.00", timestamp="2026-03-16T02:47:00Z")
        assert _compute_score(data) == 2

    def test_cross_border_adds_1(self):
        data = _validated_txn(
            amount="500.00",
            timestamp="2026-03-16T09:00:00Z",
            metadata={"channel": "api", "country": "DE"},
        )
        assert _compute_score(data) == 1

    def test_cumulative_score(self):
        # 75000 USD + 2am + cross-border = 7 + 2 + 1 = 10
        data = _validated_txn(
            amount="75000.00",
            timestamp="2026-03-16T02:00:00Z",
            metadata={"channel": "api", "country": "DE"},
        )
        assert _compute_score(data) == 10


class TestProcessMessage:
    def test_validated_transaction_gets_risk_score(self):
        msg = _make_message(_validated_txn(amount="1500.00"))
        result = process_message(msg)
        assert "fraud_risk_score" in result["data"]
        assert "fraud_risk_level" in result["data"]

    def test_rejected_transaction_passes_through(self):
        data = _validated_txn(status="rejected", rejection_reason="INVALID_CURRENCY")
        msg = _make_message(data)
        result = process_message(msg)
        assert result["data"]["status"] == "rejected"
        assert "fraud_risk_score" not in result["data"]

    def test_low_risk_transaction(self):
        msg = _make_message(_validated_txn(amount="500.00"))
        result = process_message(msg)
        assert result["data"]["fraud_risk_level"] == "LOW"
        assert result["data"]["fraud_risk_score"] == 0

    def test_medium_risk_transaction_over_10k(self):
        msg = _make_message(_validated_txn(amount="25000.00"))
        result = process_message(msg)
        assert result["data"]["fraud_risk_level"] == "MEDIUM"
        assert result["data"]["fraud_risk_score"] == 3

    def test_high_risk_transaction_over_50k(self):
        msg = _make_message(_validated_txn(amount="75000.00"))
        result = process_message(msg)
        assert result["data"]["fraud_risk_level"] == "HIGH"
        assert result["data"]["fraud_risk_score"] == 7

    def test_source_agent_set(self):
        msg = _make_message(_validated_txn())
        result = process_message(msg)
        assert result["source_agent"] == "fraud_detector"

    def test_txn004_unusual_hour_cross_border(self):
        # TXN004: 500 EUR, 02:47 UTC, country=DE → 0 + 2 + 1 = 3 → MEDIUM
        data = _validated_txn(
            transaction_id="TXN004",
            amount="500.00",
            currency="EUR",
            timestamp="2026-03-16T02:47:00Z",
            metadata={"channel": "api", "country": "DE"},
        )
        msg = _make_message(data)
        result = process_message(msg)
        assert result["data"]["fraud_risk_score"] == 3
        assert result["data"]["fraud_risk_level"] == "MEDIUM"

    def test_txn005_property_settlement_high_risk(self):
        # TXN005: 75000 USD, 10am → 7 → HIGH
        data = _validated_txn(
            transaction_id="TXN005",
            amount="75000.00",
            currency="USD",
            timestamp="2026-03-16T10:00:00Z",
        )
        msg = _make_message(data)
        result = process_message(msg)
        assert result["data"]["fraud_risk_level"] == "HIGH"
