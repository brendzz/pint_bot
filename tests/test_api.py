"""Tests for the FastAPI economy API.

These tests run against a temporary data directory; the JSON files used
by api.data_manager are monkeypatched to tmp_path so no real data is
touched.
"""
import json
import os

import pytest
from fastapi.testclient import TestClient

import api.data_manager as data_manager
from api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(data_manager, "DEBTS_FILE", tmp_path / "debts.json")
    monkeypatch.setattr(data_manager, "TRANSACTIONS_FILE", tmp_path / "transactions.json")
    monkeypatch.setattr(data_manager, "PREFERENCES_FILE", tmp_path / "preferences.json")
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def owe(client, debtor=1, creditor=2, amount="1", reason="test"):
    return client.post("/debts", json={"debtor": debtor, "creditor": creditor, "amount": amount, "reason": reason})


class TestHealthAndAuth:
    def test_health_is_open(self, client):
        assert client.get("/health").json() == {"status": "ok"}

    def test_open_access_when_api_key_unset(self, client, monkeypatch):
        monkeypatch.delenv("API_KEY", raising=False)
        assert client.get("/debts").status_code == 200

    def test_requires_key_when_set(self, client, monkeypatch):
        monkeypatch.setenv("API_KEY", "secret")
        assert client.get("/debts").status_code == 401
        assert client.get("/debts", headers={"X-API-Key": "wrong"}).status_code == 401
        assert client.get("/debts", headers={"X-API-Key": "secret"}).status_code == 200
        # Health endpoint stays open for Docker healthchecks
        assert client.get("/health").status_code == 200


class TestOweFlow:
    def test_add_and_fetch_debt(self, client):
        response = owe(client, amount="2 1/6", reason="beer")
        assert response.status_code == 200
        assert response.json()["amount"] == "13/6"

        debts = client.get("/users/1/debts").json()
        assert debts["total_owed_by_you"] == "13/6"
        assert debts["owed_by_you"]["2"][0]["reason"] == "beer"

        all_debts = client.get("/debts").json()
        assert all_debts["total_in_circulation"] == "13/6"
        assert all_debts["users"]["1"]["owes"] == "13/6"

    def test_cannot_owe_self(self, client):
        response = owe(client, debtor=1, creditor=1)
        assert response.status_code == 400
        assert response.json()["detail"] == "CANNOT_OWE_SELF"

    def test_negative_debt_rejected(self, client):
        response = owe(client, amount="-2")
        assert response.status_code == 400
        assert response.json()["detail"] == "NEGATIVE_AMOUNT"

    def test_zero_debt_rejected(self, client):
        response = owe(client, amount="0")
        assert response.status_code == 400
        assert response.json()["detail"] == "ZERO_AMOUNT"

    def test_exceeds_maximum_rejected(self, client):
        response = owe(client, amount="11")
        assert response.status_code == 400
        assert response.json()["detail"] == "EXCEEDS_MAXIMUM"

    def test_not_quantized_rejected(self, client):
        response = owe(client, amount="1/7")
        assert response.status_code == 400
        assert response.json()["detail"] == "NOT_QUANTIZED"

    @pytest.mark.parametrize("bad", ["3 -1/2", "2 7/3", "1_000", "abc", "1/0", "1/2/3", "", " "])
    def test_malformed_amounts_rejected(self, client, bad):
        response = owe(client, amount=bad)
        assert response.status_code == 400
        assert response.json()["detail"] == "INVALID_AMOUNT"

    @pytest.mark.parametrize("good,expected", [
        ("7/3", "7/3"),
        ("2 1/3", "7/3"),
        ("-2 1/2", None),  # negative -> rejected as NEGATIVE_AMOUNT, not misparsed
        ("1.5", "3/2"),
        ("1", "1"),
    ])
    def test_amount_parsing(self, client, good, expected):
        response = owe(client, amount=good)
        if expected is None:
            assert response.status_code == 400
            assert response.json()["detail"] == "NEGATIVE_AMOUNT"
        else:
            assert response.status_code == 200
            assert response.json()["amount"] == expected

    def test_invalid_debtor_id_rejected(self, client):
        response = client.post("/debts", json={"debtor": -1, "creditor": 2, "amount": "1"})
        assert response.status_code == 422


class TestSettleFlow:
    def test_settle_partial_then_full(self, client):
        owe(client, amount="2", reason="lunch")
        response = client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "1", "reason": "payback"})
        assert response.status_code == 200
        assert response.json()["settled_amount"] == "1"
        assert response.json()["remaining_amount"] == "1"

        response = client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "1"})
        assert response.json()["remaining_amount"] == "0"
        # Debt list must be empty afterwards
        assert client.get("/users/1/debts").json() == {"message": "No debts found owed to or from this user."}

    def test_settle_more_than_owed_settles_everything(self, client):
        owe(client, amount="2")
        response = client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "5"})
        assert response.status_code == 200
        assert response.json()["settled_amount"] == "2"

    def test_settle_without_debt_fails(self, client):
        response = client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "1"})
        assert response.status_code == 400
        assert response.json()["detail"] == "NO_DEBTS_FOUND"


class TestTransactions:
    def test_transactions_recorded_and_filtered(self, client):
        owe(client, amount="1", reason="beer")
        owe(client, debtor=3, creditor=1, amount="2", reason="chips")
        client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "1"})

        response = client.get("/transactions")
        assert response.status_code == 200
        txns = response.json()["transactions"]
        assert len(txns) == 3

        owes = client.get("/transactions", params={"type": "owe"}).json()["transactions"]
        assert {t["type"] for t in owes} == {"owe"}
        assert len(owes) == 2

        cashouts = client.get("/transactions", params={"type": "cashout"}).json()["transactions"]
        assert {t["type"] for t in cashouts} == {"settle"}

        user_txns = client.get("/transactions", params={"user_id": "3"}).json()["transactions"]
        assert len(user_txns) == 1
        assert user_txns[0]["debtor"] == "3"

    def test_invalid_type_rejected(self, client):
        response = client.get("/transactions", params={"type": "bogus"})
        assert response.status_code == 400
        assert response.json()["detail"] == "INVALID_TRANSACTION_TYPE"

    def test_start_after_end_rejected(self, client):
        response = client.get("/transactions", params={"start_date": "2026-12-31", "end_date": "2026-01-01"})
        assert response.status_code == 400
        assert response.json()["detail"] == "VALIDATION_ERROR"


class TestPreferences:
    def test_default_is_false_then_set_true(self, client):
        assert client.get("/users/1/unicode_preference").json() is False
        client.post("/users/1/unicode_preference", json={"use_unicode": True})
        assert client.get("/users/1/unicode_preference").json() is True


class TestSettings:
    def test_settings_shape(self, client):
        settings = client.get("/settings").json()
        for key in (
            "MAXIMUM_DEBT_CHARACTER_LIMIT",
            "MAXIMUM_PER_DEBT",
            "SMALLEST_UNIT",
            "QUANTIZE_SETTLING_DEBTS",
            "QUANTIZE_OWING_DEBTS",
            "SORT_OWES_FIRST",
        ):
            assert key in settings


class TestDataManagerResilience:
    def test_backup_created_and_restores_after_corruption(self, client, tmp_path, monkeypatch):
        debts_file = tmp_path / "debts.json"
        owe(client, amount="1")
        owe(client, amount="1")

        backup = tmp_path / "debts.json.bak"
        assert backup.exists()

        # Corrupt the main file; the backup should be used and restored
        debts_file.write_text("{ not valid json")
        response = client.get("/users/1/debts")
        assert response.status_code == 200
        assert json.loads(debts_file.read_text())["debtors"]

    def test_corrupt_file_without_backup_returns_503(self, client, tmp_path):
        (tmp_path / "debts.json").write_text("{ not valid json")
        response = client.get("/users/1/debts")
        assert response.status_code == 503
        assert response.json()["detail"] == "DATA_STORE_UNAVAILABLE"

class TestAutoReverseExcessCashouts:
    def test_excess_is_dropped_by_default(self, client):
        owe(client, debtor=1, creditor=2, amount="1")
        response = client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "2", "reason": "big cashout"})
        assert response.status_code == 200
        assert response.json()["settled_amount"] == "1"
        assert response.json()["auto_reversed_amount"] == "0"
        # No debt created in the reverse direction
        reverse = client.get("/users/2/debts").json()
        assert reverse == {"message": "No debts found owed to or from this user."}

    def test_excess_reverses_with_setting_enabled(self, client, monkeypatch):
        monkeypatch.setattr("api.config.AUTO_REVERSE_EXCESS_CASHOUTS", True)
        owe(client, debtor=1, creditor=2, amount="1")
        response = client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "2", "reason": "cashout"})
        assert response.status_code == 200
        assert response.json()["settled_amount"] == "1"
        assert response.json()["auto_reversed_amount"] == "1"

        # Alice's debt is settled; Bob now owes Alice the excess
        alice = client.get("/users/1/debts").json()
        assert alice["total_owed_to_you"] == "1"
        assert alice["owed_to_you"]["2"][0]["amount"] == "1"

        bob = client.get("/users/2/debts").json()
        assert bob["total_owed_by_you"] == "1"

    def test_reverse_creates_an_owe_transaction(self, client, monkeypatch):
        monkeypatch.setattr("api.config.AUTO_REVERSE_EXCESS_CASHOUTS", True)
        owe(client, debtor=1, creditor=2, amount="1")
        client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "3"})
        txns = client.get("/transactions").json()["transactions"]
        reverse = [t for t in txns if t["type"] == "owe" and t["debtor"] == "2"]
        assert len(reverse) == 1
        assert reverse[0]["amount"] == "2"
        assert reverse[0]["creditor"] == "1"

    def test_settle_below_owed_does_not_reverse(self, client, monkeypatch):
        monkeypatch.setattr("api.config.AUTO_REVERSE_EXCESS_CASHOUTS", True)
        owe(client, debtor=1, creditor=2, amount="5")
        response = client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "2"})
        assert response.json()["auto_reversed_amount"] == "0"
        assert response.json()["remaining_amount"] == "3"
        # No debt created for the other side (Bob owes Alice nothing)
        bob = client.get("/users/2/debts").json()
        assert bob["total_owed_by_you"] == "0"
        assert bob["owed_by_you"] == {}

    def test_settings_expose_new_flags(self, client):
        settings = client.get("/settings").json()
        assert "AUTO_REVERSE_EXCESS_CASHOUTS" in settings
        assert "AUDIT_LOG_ENABLED" in settings
        assert settings["AUTO_REVERSE_EXCESS_CASHOUTS"] is False
        assert settings["AUDIT_LOG_ENABLED"] is False


class TestAuditLog:
    @pytest.fixture
    def captured_webhook(self, monkeypatch):
        calls = []

        async def fake_post(url, content):
            calls.append({"url": url, "content": content})

        monkeypatch.setattr("api.audit._post_webhook", fake_post)
        monkeypatch.setenv("AUDIT_LOG_WEBHOOK_URL", "https://example.invalid/webhook")
        return calls

    def test_audit_disabled_by_default(self, client, monkeypatch):
        calls = []

        async def fake_post(url, content):
            calls.append(content)

        monkeypatch.setattr("api.audit._post_webhook", fake_post)
        monkeypatch.delenv("AUDIT_LOG_WEBHOOK_URL", raising=False)
        owe(client, amount="1")
        assert calls == []

    def test_owe_and_settle_are_audited(self, client, captured_webhook):
        owe(client, debtor=1, creditor=2, amount="1", reason="beer")
        client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "1"})
        assert len(captured_webhook) == 2
        assert "**OWE**" in captured_webhook[0]["content"]
        assert "1 → 2" in captured_webhook[0]["content"]
        assert "beer" in captured_webhook[0]["content"]
        assert "**SETTLE**" in captured_webhook[1]["content"]
        assert captured_webhook[0]["url"] == "https://example.invalid/webhook"

    def test_audit_includes_auto_reverse_transaction(self, client, captured_webhook, monkeypatch):
        monkeypatch.setattr("api.config.AUTO_REVERSE_EXCESS_CASHOUTS", True)
        owe(client, debtor=1, creditor=2, amount="1")
        captured_webhook.clear()
        client.patch("/debts", json={"debtor": 1, "creditor": 2, "amount": "3"})
        assert len(captured_webhook) == 2  # settle + reversed owe
        assert any("**OWE**" in c["content"] and "2 → 1" in c["content"] for c in captured_webhook)

    def test_audit_failure_does_not_break_transaction(self, client, monkeypatch):
        async def failing_post(url, content):
            raise RuntimeError("webhook down")

        monkeypatch.setattr("api.audit._post_webhook", failing_post)
        monkeypatch.setenv("AUDIT_LOG_WEBHOOK_URL", "https://example.invalid/webhook")
        response = owe(client, amount="1")
        assert response.status_code == 200
        assert client.get("/users/1/debts").json()["total_owed_by_you"] == "1"

    def test_webhook_payload_blocks_mentions(self):
        from api import audit
        import inspect
        source = inspect.getsource(audit._post_webhook)
        assert '"allowed_mentions"' in source
        assert '"parse": []' in source
