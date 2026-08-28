from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from backend.app.graph.alerts import (alert_layering, alert_night_bursts,
                                      alert_structuring)
from backend.app.nlp.entity_extractor import EntityExtractor
from backend.app.ingestion.loaders import load_registry
from scripts.run_pipeline import run


@pytest.fixture(scope="module")
def analytics():
    return run()


def _tx(ts, frm, to, amount, mode="neft"):
    return {"timestamp": ts, "from_account": frm, "to_account": to,
            "amount_inr": amount, "mode": mode}


class TestExtraction:
    def setup_method(self):
        self.ex = EntityExtractor(load_registry(Path("data/sample/registry.json")))

    def test_phone_extraction(self):
        ents = self.ex.extract("caller used number 9812345678 repeatedly")
        phones = [e["value"] for e in ents if e["type"] == "phone"]
        assert "9812345678" in phones

    def test_vehicle_plate(self):
        ents = self.ex.extract("car UP32AB4455 was intercepted")
        assert any(e["type"] == "vehicle" and e["value"] == "UP32AB4455" for e in ents)

    def test_alias_resolution(self):
        ents = self.ex.extract("kingpin Bunty met Munna near market")
        pids = {e.get("canonical_id") for e in ents if e["type"] == "person"}
        assert {"P001", "P020"} <= pids

    def test_surname_resolution(self):
        pid = self.ex._resolve_person("Munna Gupta")
        assert pid == "P020"

    def test_noise_filtered(self):
        ents = self.ex.extract("the driver and broker met at account ACC2002")
        persons = [e["value"].lower() for e in ents if e["type"] == "person"]
        assert "Driver" not in persons and not any("ACC" in p.upper() for p in persons)


class TestAnalytics:
    def test_pipeline_runs(self, analytics):
        assert analytics["stats"]["nodes"] > 40
        assert len(analytics["influencers"]) > 10

    def test_bridge_found(self, analytics):
        labels = [b["label"] for b in analytics["bridges"]]
        assert "Manoj Gupta" in labels

    def test_cyber_cell_isolated(self, analytics):
        for comm in analytics["communities"]:
            members = {m["label"] for m in comm["members"]}
            if {"Prakash Rao", "Imran Sheikh"} <= members:
                assert "Vikram Shukla" not in members

    def test_influencer_risk_flags(self, analytics):
        by_label = {r["label"]: r for r in analytics["influencers"]}
        assert by_label["Neha Kulkarni"]["risk_points"] >= 2


class TestAlerts:
    def test_structuring_detected(self):
        rows = [_tx(f"2026-03-0{d} 11:00:00", "CASH", "ACCX", 49500, "cash_deposit")
                for d in range(1, 7)]
        alerts = alert_structuring(rows)
        assert len(alerts) == 1 and alerts[0]["accounts"] == ["ACCX"]

    def test_no_structuring_above_threshold(self):
        rows = [_tx("2026-03-01 11:00:00", "CASH", "ACCX", 99000, "cash_deposit")]
        assert alert_structuring(rows) == []

    def test_layering_chain(self):
        rows = [
            _tx("2026-01-01 09:00:00", "A", "B", 100000),
            _tx("2026-01-01 10:00:00", "B", "C", 98000),
            _tx("2026-01-01 11:00:00", "C", "D", 95000),
        ]
        alerts = alert_layering(rows)
        assert any(a["severity"] == "high" for a in alerts)

    def test_night_burst(self):
        rows = [{"timestamp": f"2026-01-01 02:{m:02d}:00", "caller_number": "9000000000",
                 "callee_number": "9111111111", "duration_sec": 600}
                for m in range(30)]
        alerts = alert_night_bursts(rows)
        assert len(alerts) == 1 and alerts[0]["evidence"]["night_calls"] == 30
