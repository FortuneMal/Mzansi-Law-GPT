"""Checks that the golden set is well formed and grounded in the chunks the ingestion pipeline produces."""
import collections
import json
import os

import pytest

import metrics
from conftest import REPO_ROOT

GOLDEN = os.path.join(REPO_ROOT, "evals", "golden_set.jsonl")
RAW_ACTS = os.path.join(REPO_ROOT, "data", "raw_acts")
FIELDS = {"id", "category", "question", "expected_acts", "expected_facts", "reference_points", "reviewed"}


@pytest.fixture(scope="module")
def golden():
    with open(GOLDEN, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@pytest.fixture(scope="module")
def corpus_chunks():
    from data_ingestion import load_and_chunk_text
    docs = []
    for name in sorted(os.listdir(RAW_ACTS)):
        if name.endswith(".txt"):
            docs.extend(load_and_chunk_text(os.path.join(RAW_ACTS, name)))
    return docs


def test_schema_and_categories(golden):
    assert all(set(r) == FIELDS for r in golden)
    assert len({r["id"] for r in golden}) == len(golden)
    counts = collections.Counter(r["category"] for r in golden)
    assert set(counts) == {"answerable", "multi_act", "out_of_scope", "adversarial"}
    assert all(isinstance(r["reviewed"], bool) for r in golden)
    assert all(r["reference_points"] for r in golden)


def test_expected_acts_match_ingestion_titles(golden, corpus_chunks):
    titles = {d.metadata["act"] for d in corpus_chunks}
    for r in golden:
        for act in r["expected_acts"]:
            assert act in titles, f"{r['id']}: unknown act title {act!r}"


def test_expected_facts_exist_in_expected_act_text(golden, corpus_chunks):
    for r in golden:
        texts = [metrics.normalise(d.page_content) for d in corpus_chunks if d.metadata["act"] in r["expected_acts"]]
        for fact in r["expected_facts"]:
            assert any(metrics._contains(t, fact) for t in texts), f"{r['id']}: fact {fact!r} not in corpus"


def test_out_of_scope_items_have_no_expected_facts(golden):
    for r in golden:
        if r["category"] == "out_of_scope":
            assert r["expected_facts"] == []
