"""Runner helpers that do not need network: judge parsing and report rendering."""
import json

import run_evals
from conftest import make_client

ITEM = {"id": "x", "category": "answerable", "question": "q", "reference_points": ["p1"]}
OOS = dict(ITEM, category="out_of_scope")


def test_judge_computes_faithfulness_from_claims_and_clamps():
    client, completions = make_client(json_content=json.dumps({
        "claims": [{"claim": "c1", "supported": True}, {"claim": "c2", "supported": False},
                   {"claim": "c3", "supported": True}, {"claim": "c4"}],  # missing flag counts as unsupported
        "faithfulness": 1.0,  # ignored: computed from claims
        "relevance": "1.7", "reference_coverage": None, "states_not_covered": True, "rationale": "r"}))
    j = run_evals.judge_answer(client, ITEM, "ctx", "ans")
    assert j["faithfulness"] == 0.5
    assert j["claims_total"] == 4
    assert j["unsupported_claims"] == ["c2", "c4"]
    assert j["relevance"] == 1.0 and j["reference_coverage"] is None
    assert j["abstained_correctly"] is None  # only meaningful for out_of_scope
    call = completions.calls[0]
    assert call["temperature"] == 0 and call["response_format"] == {"type": "json_object"}
    assert call["model"] == "gpt-4o-mini"


def _oos_verdict(claims, states_not_covered):
    client, _ = make_client(json_content=json.dumps({"claims": claims, "relevance": 1, "reference_coverage": 1,
                                                     "states_not_covered": states_not_covered}))
    return run_evals.judge_answer(client, OOS, "ctx", "ans")


def test_abstention_is_derived_from_disclosure_and_unsupported_claims():
    supported = [{"claim": "s", "supported": True}]
    invented = [{"claim": "made-up rule", "supported": False}]
    assert _oos_verdict([], True)["abstained_correctly"] is True
    assert _oos_verdict(supported, True)["abstained_correctly"] is True
    assert _oos_verdict(invented, True)["abstained_correctly"] is False   # disclosed, then answered anyway
    assert _oos_verdict([], False)["abstained_correctly"] is False        # never said it is not covered
    assert _oos_verdict([], "yes")["abstained_correctly"] is None         # malformed -> not scored
    assert _oos_verdict([], True)["faithfulness"] == 1.0


def test_judge_errors_are_captured():
    client, _ = make_client(json_content="not json")
    assert "error" in run_evals.judge_answer(client, ITEM, "ctx", "ans")
    client, _ = make_client(json_content=json.dumps({"faithfulness": 1}))
    assert "claims" in run_evals.judge_answer(client, ITEM, "ctx", "ans")["error"]
    client, _ = make_client(error=RuntimeError("rate limited"))
    assert "rate limited" in run_evals.judge_answer(client, ITEM, "ctx", "ans")["error"]


def test_render_markdown_lists_failures():
    results = [
        {"id": "ok", "category": "answerable", "act_hit": True, "fact_hit": 1.0, "missing_facts": [],
         "citation": {"unsupported": [], "clean": True}, "retrieved": [{"act": "A"}],
         "judge": {"faithfulness": 1, "relevance": 1, "reference_coverage": 1, "unsupported_claims": []}},
        {"id": "bad", "category": "answerable", "act_hit": False, "fact_hit": 0.0, "missing_facts": ["f|1"],
         "citation": {"unsupported": [], "clean": True}, "retrieved": [{"act": "B"}],
         "judge": {"faithfulness": 1, "relevance": 1, "reference_coverage": 1, "unsupported_claims": ["made up"]}},
    ]
    import metrics
    report = {"meta": {"run_id": "r", "git_revision": "g", "collection": "c", "backend": "cloud", "collection_points": 1,
                       "chat_model": "m", "judge_model": "m", "retrieval_k": 4, "golden_set_sha256": "0" * 64,
                       "category_filter": None, "limit": None},
              "aggregate": metrics.aggregate(results), "by_category": metrics.aggregate_by_category(results),
              "results": results}
    md = run_evals.render_markdown(report)
    assert "## Failing questions (1 of 2)" in md
    assert "| bad | answerable | retrieval | B |" in md
    assert "f\\|1" in md  # pipes in reasons are escaped
    assert "**bad**: made up" in md
