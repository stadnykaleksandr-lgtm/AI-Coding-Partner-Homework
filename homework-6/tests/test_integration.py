"""Integration tests — full pipeline end-to-end."""
import json
from pathlib import Path

import pytest

from integrator import run_pipeline


SAMPLE_TRANSACTIONS_PATH = Path(__file__).parent.parent / "sample-transactions.json"


class TestFullPipeline:
    def test_all_8_transactions_produce_result_files(self, tmp_path):
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        result_files = list(tmp_path.glob("*.json"))
        assert len(result_files) == 8

    def test_all_8_transactions_returned(self, tmp_path):
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        assert len(results) == 8

    def test_every_result_has_status(self, tmp_path):
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        for msg in results:
            assert "status" in msg["data"]

    def test_valid_statuses_only(self, tmp_path):
        allowed = {"settled", "held_for_review", "rejected", "error"}
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        for msg in results:
            assert msg["data"]["status"] in allowed

    def test_txn001_monthly_rent_settled(self, tmp_path):
        # 1500 USD, US domestic, 9am → LOW → settled
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        txn = next(m for m in results if m["data"]["transaction_id"] == "TXN001")
        assert txn["data"]["status"] == "settled"
        assert txn["data"]["fraud_risk_level"] == "LOW"

    def test_txn002_equipment_purchase_medium_risk(self, tmp_path):
        # 25000 USD → score 3 → MEDIUM → settled
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        txn = next(m for m in results if m["data"]["transaction_id"] == "TXN002")
        assert txn["data"]["status"] == "settled"
        assert txn["data"]["fraud_risk_level"] == "MEDIUM"

    def test_txn005_property_settlement_held(self, tmp_path):
        # 75000 USD → score 7 → HIGH → held_for_review
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        txn = next(m for m in results if m["data"]["transaction_id"] == "TXN005")
        assert txn["data"]["status"] == "held_for_review"
        assert txn["data"]["fraud_risk_level"] == "HIGH"

    def test_txn006_invalid_currency_rejected(self, tmp_path):
        # XYZ currency → rejected
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        txn = next(m for m in results if m["data"]["transaction_id"] == "TXN006")
        assert txn["data"]["status"] == "rejected"
        assert txn["data"]["rejection_reason"] == "INVALID_CURRENCY"

    def test_txn007_negative_amount_rejected(self, tmp_path):
        # -100.00 GBP → rejected
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        txn = next(m for m in results if m["data"]["transaction_id"] == "TXN007")
        assert txn["data"]["status"] == "rejected"
        assert txn["data"]["rejection_reason"] == "INVALID_AMOUNT"

    def test_result_files_are_valid_json(self, tmp_path):
        run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        for path in tmp_path.glob("*.json"):
            with open(path) as f:
                data = json.load(f)
            assert "data" in data
            assert "transaction_id" in data["data"]

    def test_txn004_unusual_hour_cross_border(self, tmp_path):
        # 500 EUR, 02:47 UTC, DE → score 3 → MEDIUM → settled
        results = run_pipeline(SAMPLE_TRANSACTIONS_PATH, results_dir=tmp_path)
        txn = next(m for m in results if m["data"]["transaction_id"] == "TXN004")
        assert txn["data"]["status"] == "settled"
        assert txn["data"]["fraud_risk_level"] == "MEDIUM"
