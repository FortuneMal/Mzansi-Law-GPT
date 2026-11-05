import json

import query_log


def test_disabled_writes_nothing(query_log_path, monkeypatch):
    monkeypatch.delenv("MZANSI_LOG_QUERIES", raising=False)
    query_log.log_rag_event({"query": "q"})
    monkeypatch.setenv("MZANSI_LOG_QUERIES", "true")  # only the exact value "1" enables logging
    query_log.log_rag_event({"query": "q"})
    assert not query_log_path.exists()


def test_enabled_appends_one_json_line_per_event(query_log_path, monkeypatch):
    monkeypatch.setenv("MZANSI_LOG_QUERIES", "1")
    query_log.log_rag_event({"endpoint": "/api/chat", "query": "Hoeveel verlof?", "sources": [{"act": "A", "section": "1"}]})
    query_log.log_rag_event({"endpoint": "/api/chat/stream", "query": "q2", "timestamp": "fixed"})
    lines = query_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first, second = map(json.loads, lines)
    assert first["endpoint"] == "/api/chat" and first["sources"] == [{"act": "A", "section": "1"}]
    assert "timestamp" in first
    assert second["timestamp"] == "fixed"


def test_unserialisable_values_are_stringified(query_log_path, monkeypatch):
    monkeypatch.setenv("MZANSI_LOG_QUERIES", "1")
    query_log.log_rag_event({"obj": object()})
    assert json.loads(query_log_path.read_text(encoding="utf-8"))["obj"].startswith("<object")


def test_failures_are_swallowed_with_a_single_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MZANSI_LOG_QUERIES", "1")
    monkeypatch.setattr(query_log, "_warned", False)
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("x")
    monkeypatch.setattr(query_log, "LOG_PATH", str(blocker / "queries.jsonl"))  # parent is a file -> OSError
    query_log.log_rag_event({"query": "q"})
    query_log.log_rag_event({"query": "q"})
    err = capsys.readouterr().err
    assert err.count("[WARN] query logging failed") == 1
