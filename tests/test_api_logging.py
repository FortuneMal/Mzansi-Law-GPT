"""Endpoint tests with Qdrant and OpenAI replaced by fakes: response shape and query-log integration."""
import json

import pytest
from fastapi.testclient import TestClient

import api_server
import rag_core
from conftest import FakeVectorStore, make_client


@pytest.fixture
def wired(monkeypatch, sample_docs, query_log_path):
    """Patches the vector store and OpenAI client; returns a function that sets the fake client."""
    vs = FakeVectorStore(sample_docs)
    monkeypatch.setattr(rag_core, "get_qdrant_vector_store", lambda **kw: vs)

    def set_client(**kwargs):
        client, completions = make_client(**kwargs)
        monkeypatch.setattr(api_server, "get_openai_client", lambda: client)
        return completions

    set_client()
    monkeypatch.setenv("MZANSI_LOG_QUERIES", "1")
    return set_client


def _log_lines(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_chat_response_shape_and_log(wired, query_log_path):
    wired(answer="  Grounded answer. \n")
    resp = TestClient(api_server.app).post("/api/chat", json={"query": "How many hours?"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"answer", "sources", "timestamp"}
    assert body["answer"] == "Grounded answer."
    assert set(body["sources"][0]) == {"act", "section", "content", "source_file"}

    (event,) = _log_lines(query_log_path)
    assert event["endpoint"] == "/api/chat"
    assert event["query"] == "How many hours?"
    assert event["act_filter"] == "All Acts"
    assert event["collection"] == "mzansi_law_acts_v2"
    assert event["sources"][0] == {"act": "BASIC CONDITIONS OF EMPLOYMENT ACT 75 OF 1997 (BCEA)", "section": "9"}
    assert event["answer"] == "Grounded answer."
    assert event["model"] == "gpt-4o-mini"
    assert event["error"] is None
    assert isinstance(event["latency_ms"], float)
    assert set(event) == {"timestamp", "endpoint", "query", "act_filter", "collection", "sources", "answer", "model", "latency_ms", "error"}


def test_stream_accumulates_deltas_and_logs_once_after_done(wired, query_log_path):
    wired(deltas=("The ", "answer", " text."))
    resp = TestClient(api_server.app).post("/api/chat/stream", json={"query": "q"})
    events = [json.loads(x) for x in resp.text.splitlines()]
    assert [e["type"] for e in events] == ["sources", "delta", "delta", "delta", "done"]
    assert "".join(e["content"] for e in events if e["type"] == "delta") == "The answer text."

    (event,) = _log_lines(query_log_path)
    assert event["endpoint"] == "/api/chat/stream"
    assert event["answer"] == "The answer text."
    assert event["error"] is None


def test_stream_error_is_logged_once_with_partial_answer(wired, query_log_path):
    wired(deltas=("partial",), stream_error=RuntimeError("upstream died"))
    resp = TestClient(api_server.app).post("/api/chat/stream", json={"query": "q"})
    events = [json.loads(x) for x in resp.text.splitlines()]
    assert events[-1] == {"type": "error", "detail": "upstream died"}

    (event,) = _log_lines(query_log_path)
    assert event["answer"] == "partial"
    assert event["error"] == "upstream died"


def test_vector_store_failure_returns_same_500_and_is_logged(monkeypatch, wired, query_log_path):
    def boom(**kw):
        raise ValueError("no route to host")
    monkeypatch.setattr(rag_core, "get_qdrant_vector_store", boom)
    for path in ("/api/chat", "/api/chat/stream"):
        resp = TestClient(api_server.app).post(path, json={"query": "q"})
        assert resp.status_code == 500
        assert resp.json() == {"detail": "Failed to connect to Qdrant Vector Store: no route to host"}
    events = _log_lines(query_log_path)
    assert [e["endpoint"] for e in events] == ["/api/chat", "/api/chat/stream"]
    assert all("no route to host" in e["error"] for e in events)


def test_logging_disabled_writes_nothing(monkeypatch, wired, query_log_path):
    monkeypatch.delenv("MZANSI_LOG_QUERIES")
    client = TestClient(api_server.app)
    assert client.post("/api/chat", json={"query": "q"}).status_code == 200
    assert client.post("/api/chat/stream", json={"query": "q"}).status_code == 200
    assert not query_log_path.exists()


def test_logging_failure_does_not_break_request(monkeypatch, wired):
    import query_log

    def explode(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(query_log, "open", explode, raising=False)
    resp = TestClient(api_server.app).post("/api/chat", json={"query": "q"})
    assert resp.status_code == 200


def test_retrieve_sources_shared_path(monkeypatch, sample_docs):
    vs = FakeVectorStore(sample_docs)
    monkeypatch.setattr(rag_core, "get_qdrant_vector_store", lambda **kw: vs)
    sources, context, messages = rag_core.retrieve_sources(rag_core.ChatRequest(query="q", act_filter="POPIA"))
    assert vs.calls == [("POPIA: q", 4)]
    assert [s.act for s in sources] == ["PROTECTION OF PERSONAL INFORMATION ACT 4 OF 2013 (POPIA)"]
    assert context.startswith("Source: PROTECTION OF PERSONAL INFORMATION ACT")
    assert messages[0]["role"] == "system" and messages[-1]["role"] == "user"
    assert context in messages[-1]["content"]


def test_generate_answer_uses_chat_settings():
    client, completions = make_client(answer=" x ")
    assert rag_core.generate_answer([{"role": "user", "content": "q"}], client) == "x"
    assert completions.calls[0]["model"] == "gpt-4o-mini"
    assert completions.calls[0]["temperature"] == 0.2
