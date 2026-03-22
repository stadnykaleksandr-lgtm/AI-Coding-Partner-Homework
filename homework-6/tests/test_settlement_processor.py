"""Unit tests for Settlement Processor Agent."""
import json
import pytest
from agents.settlement_processor import process_message


def _make_message(data: dict) -> dict:
    return {
        "message_id": "test-003",
        "timestamp": "2026-03-16T10:00:00Z",
        "source_agent": "fraud_detector",
        "target_agent": "settlement_processor",
        "message_type": "transaction",
        "data": data,
    }


def _scored_txn(risk_level: str, **overrides) -> dict:
    base = {
        "transaction_id": "TXN001",
        "amount": "1500.00",
        "currency": "USD",
        "source_account": "ACC-1001",
        "destination_account": "ACC-2001",
        "status": "validated",
        "fraud_risk_score": 0,
        "fraud_risk_level": risk_level,
    }
    base.update(overrides)
    return base


class TestSettlement:
    def test_low_risk_is_settled(self, tmp_path):
        msg = _make_message(_scored_txn("LOW"))
        result = process_message(msg, results_dir=tmp_path)
        assert result["data"]["status"] == "settled"

    def test_medium_risk_is_settled(self, tmp_path):
        msg = _make_message(_scored_txn("MEDIUM"))
        result = process_message(msg, results_dir=tmp_path)
        assert result["data"]["status"] == "settled"

    def test_high_risk_is_held(self, tmp_path):
        msg = _make_message(_scored_txn("HIGH"))
        result = process_message(msg, results_dir=tmp_path)
        assert result["data"]["status"] == "held_for_review"

    def test_rejected_passes_through(self, tmp_path):
        data = {
            "transaction_id": "TXN006",
            "amount": "200.00",
            "currency": "XYZ",
            "source_account": "ACC-1006",
            "destination_account": "ACC-7700",
            "status": "rejected",
            "rejection_reason": "INVALID_CURRENCY",
        }
        msg = _make_message(data)
        result = process_message(msg, results_dir=tmp_path)
        assert result["data"]["status"] == "rejected"

    def test_source_agent_set(self, tmp_path):
        msg = _make_message(_scored_txn("LOW"))
        result = process_message(msg, results_dir=tmp_path)
        assert result["source_agent"] == "settlement_processor"


class TestResultFileWritten:
    def test_result_file_created(self, tmp_path):
        msg = _make_message(_scored_txn("LOW", transaction_id="TXN001"))
        process_message(msg, results_dir=tmp_path)
        result_file = tmp_path / "TXN001.json"
        assert result_file.exists()

    def test_result_file_contains_valid_json(self, tmp_path):
        msg = _make_message(_scored_txn("MEDIUM", transaction_id="TXN002"))
        process_message(msg, results_dir=tmp_path)
        result_file = tmp_path / "TXN002.json"
        with open(result_file) as f:
            data = json.load(f)
        assert data["data"]["status"] == "settled"

    def test_result_file_for_held_transaction(self, tmp_path):
        msg = _make_message(_scored_txn("HIGH", transaction_id="TXN005"))
        process_message(msg, results_dir=tmp_path)
        result_file = tmp_path / "TXN005.json"
        with open(result_file) as f:
            data = json.load(f)
        assert data["data"]["status"] == "held_for_review"

    def test_result_dir_created_if_not_exists(self, tmp_path):
        nested = tmp_path / "deep" / "results"
        msg = _make_message(_scored_txn("LOW", transaction_id="TXN001"))
        process_message(msg, results_dir=nested)
        assert (nested / "TXN001.json").exists()

    def test_rejected_result_file_written(self, tmp_path):
        data = {
            "transaction_id": "TXN007",
            "status": "rejected",
            "rejection_reason": "INVALID_AMOUNT",
            "amount": "-100.00",
            "currency": "GBP",
            "source_account": "ACC-1007",
            "destination_account": "ACC-8800",
        }
        msg = _make_message(data)
        process_message(msg, results_dir=tmp_path)
        result_file = tmp_path / "TXN007.json"
        assert result_file.exists()
        with open(result_file) as f:
            saved = json.load(f)
        assert saved["data"]["status"] == "rejected"
