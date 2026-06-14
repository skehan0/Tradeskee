import types
from datetime import datetime

import pytest

import src.LLM.LLM_service as llm_service


class DummyCollection:
    def __init__(self):
        self.calls = []

    def update_one(self, filter_q, update_q, upsert=False):
        self.calls.append((filter_q, update_q, upsert))
        return types.SimpleNamespace(matched_count=1)


class DummyDB:
    def __init__(self):
        self.analyses = DummyCollection()


def test_store_analysis_monkeypatch(monkeypatch):
    dummy_db = DummyDB()
    monkeypatch.setattr(llm_service, "db", dummy_db)

    symbol = "FOO"
    analysis = "sample analysis"
    llm_service.store_analysis(symbol, analysis)

    assert len(dummy_db.analyses.calls) == 1
    filter_q, update_q, upsert = dummy_db.analyses.calls[0]
    assert filter_q == {"symbol": symbol}
    assert "analysis" in update_q["$set"]
    assert update_q["$set"]["analysis"] == analysis
