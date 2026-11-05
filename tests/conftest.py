import os
import sys
from types import SimpleNamespace as NS

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (REPO_ROOT, os.path.join(REPO_ROOT, "evals")):
    if p not in sys.path:
        sys.path.insert(0, p)


class FakeVectorStore:
    """Stands in for QdrantVectorStore; returns fixed documents and records queries."""

    def __init__(self, docs):
        self.docs = docs
        self.calls = []

    def similarity_search(self, query, k):
        self.calls.append((query, k))
        return list(self.docs)[:k]


class FakeCompletions:
    """Stands in for client.chat.completions. Configure .answer, .deltas, .stream_error or .json_content."""

    def __init__(self, answer="An answer.", deltas=("Hel", "lo"), stream_error=None, json_content=None, error=None):
        self.answer = answer
        self.deltas = deltas
        self.stream_error = stream_error
        self.json_content = json_content
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        if kwargs.get("stream"):
            def gen():
                for d in self.deltas:
                    yield NS(choices=[NS(delta=NS(content=d))])
                if self.stream_error:
                    raise self.stream_error
            return gen()
        content = self.json_content if self.json_content is not None else self.answer
        return NS(choices=[NS(message=NS(content=content))])


def make_client(**kwargs):
    completions = FakeCompletions(**kwargs)
    return NS(chat=NS(completions=completions)), completions


@pytest.fixture
def sample_docs():
    from langchain_core.documents import Document
    return [
        Document(page_content="Section 9: Ordinary Hours of Work ... 45 hours in any week",
                 metadata={"act": "BASIC CONDITIONS OF EMPLOYMENT ACT 75 OF 1997 (BCEA)", "section": "9", "source": "bcea_act_75_of_1997.txt"}),
        Document(page_content="Section 14: Retention ...",
                 metadata={"act": "PROTECTION OF PERSONAL INFORMATION ACT 4 OF 2013 (POPIA)", "section": "Chunk_1", "source": "popia_act_4_of_2013.txt"}),
    ]


@pytest.fixture
def query_log_path(tmp_path, monkeypatch):
    import query_log
    path = tmp_path / "logs" / "queries.jsonl"
    monkeypatch.setattr(query_log, "LOG_PATH", str(path))
    monkeypatch.setattr(query_log, "_warned", False)
    return path
