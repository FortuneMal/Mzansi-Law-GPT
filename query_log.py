"""Opt-in JSONL query logging for the RAG chat endpoints.

Set MZANSI_LOG_QUERIES=1 to append one JSON object per chat request to
logs/queries.jsonl. With the variable unset (or any other value) this module
does nothing. Logging never raises into the request path: any failure is
swallowed and reported once on stderr.

log_rag_event is the single integration point for a future external
evaluation or observability service. Keep it free of network dependencies.

Event fields written by the API: timestamp, endpoint, query, act_filter,
collection, sources (list of {act, section}), answer, model, latency_ms, error.
"""
import json
import os
import sys
import threading
from datetime import datetime, timezone

ENV_FLAG = "MZANSI_LOG_QUERIES"
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "queries.jsonl")

_write_lock = threading.Lock()
_warned = False


def logging_enabled() -> bool:
    return os.getenv(ENV_FLAG) == "1"


def log_rag_event(event: dict) -> None:
    """Appends one JSON line describing a RAG request to logs/queries.jsonl when MZANSI_LOG_QUERIES=1."""
    global _warned
    if not logging_enabled():
        return
    try:
        record = dict(event)
        record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        line = json.dumps(record, ensure_ascii=False, default=str)
        with _write_lock:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception as e:  # never let logging break a request
        if not _warned:
            _warned = True
            try:
                print(f"[WARN] query logging failed, further logging errors suppressed: {e!r}", file=sys.stderr)
            except Exception:
                pass
