import metrics

BCEA = "BASIC CONDITIONS OF EMPLOYMENT ACT 75 OF 1997 (BCEA)"
POPIA = "PROTECTION OF PERSONAL INFORMATION ACT 4 OF 2013 (POPIA)"
LRA = "LABOUR RELATIONS ACT 66 OF 1995 (LRA)"


def test_normalise_folds_case_punctuation_and_whitespace():
    assert metrics.normalise("Three  Days’ paid-leave,\n(a)") == "three days paid leave a"
    assert metrics.normalise(None) == ""


def test_act_hit_any_expected_act():
    assert metrics.act_hit([BCEA, LRA], [POPIA, LRA]) is True
    assert metrics.act_hit([BCEA], [POPIA]) is False
    assert metrics.act_hit([], [POPIA]) is None
    # tolerant of case and punctuation differences
    assert metrics.act_hit(["basic conditions of employment act 75 of 1997 bcea"], [BCEA]) is True


def test_act_recall_fraction():
    assert metrics.act_recall([BCEA, LRA], [BCEA, POPIA]) == 0.5
    assert metrics.act_recall([BCEA], []) == 0.0
    assert metrics.act_recall([], [BCEA]) is None


def test_fact_hit_fraction_and_missing():
    ctx = "An employer may not require ... more than (a) 45 hours in any week; and\n(b) nine hours in any day"
    facts = ["45 hours in any week", "Nine hours in any day", "eight hours in any day"]
    assert metrics.fact_hit(facts, ctx) == 2 / 3
    assert metrics.missing_facts(facts, ctx) == ["eight hours in any day"]
    assert metrics.fact_hit([], ctx) is None


def test_fact_hit_is_word_bounded():
    # "10 hours" must not match inside "110 hours"
    assert metrics.fact_hit(["10 hours"], "work 110 hours") == 0.0
    assert metrics.fact_hit(["over-indebted"], "would make the consumer over-indebted.") == 1.0


def test_extract_act_mentions_names_abbreviations_and_numbers():
    text = ("Under the BCEA and the Labour Relations Act, read with Act 4 of 2013 and section 23 of the "
            "Constitution. The Constitutional Court agreed. See also the Rental Housing Act 50 of 1999. The Act says so.")
    found = metrics.extract_act_mentions(text)
    assert {"bcea", "lra", "popia", "constitution"} <= found
    assert "other:rental housing act" in found
    assert not any(k == "other:act" for k in found)
    assert len([k for k in found if k.startswith("other:")]) == 1


def test_extract_act_mentions_masks_longer_names():
    found = metrics.extract_act_mentions("Regulation 4 of the POPIA General Regulations applies.")
    assert found == {"popia_regs"}


def test_extract_act_mentions_lowercase_constitution_is_not_an_act():
    assert metrics.extract_act_mentions("join a trade union, subject to its constitution") == set()


def test_citation_check_flags_unsupported_acts():
    sources = [{"act": BCEA, "source_file": "bcea_act_75_of_1997.txt"}]
    res = metrics.citation_check("Per the BCEA and the Labour Relations Act ...", sources, "Section 9 ...")
    assert res["retrieved"] == ["bcea"]
    assert res["unsupported"] == ["lra"]
    assert res["clean"] is False


def test_citation_check_accepts_acts_named_in_retrieved_text():
    sources = [{"act": LRA, "source_file": "lra_act_66_of_1995.txt"}]
    ctx = "to give effect to ... section 23 of the Constitution"
    res = metrics.citation_check("The LRA gives effect to the Constitution.", sources, ctx)
    assert res["cited_not_retrieved"] == ["constitution"]
    assert res["unsupported"] == []
    assert res["clean"] is True


def test_source_key_falls_back_to_title():
    assert metrics.source_key(BCEA, "unknown.txt") == "bcea"
    assert metrics.source_key("Something Else", "x.txt") == "other:something else"


def _result(**kw):
    base = {"id": "q", "category": "answerable", "act_hit": True, "fact_hit": 1.0, "missing_facts": [],
            "citation": {"unsupported": [], "clean": True},
            "judge": {"faithfulness": 1.0, "relevance": 1.0, "reference_coverage": 1.0, "unsupported_claims": [], "abstained_correctly": None}}
    base.update(kw)
    return base


def test_failure_reasons_and_stage():
    assert metrics.failure_reasons(_result()) == []
    assert metrics.failure_stage(_result()) == "pass"
    r = _result(act_hit=False, fact_hit=0.5, missing_facts=["x"])
    assert metrics.failure_stage(r) == "retrieval"
    assert any("missing facts x" in s for s in metrics.failure_reasons(r))
    r = _result(judge={"faithfulness": 0.2, "relevance": 0.9, "reference_coverage": 0.9})
    assert metrics.failure_stage(r) == "generation"
    oos = _result(category="out_of_scope", act_hit=None, fact_hit=None,
                  judge={"faithfulness": 0.0, "abstained_correctly": False})
    assert metrics.failure_reasons(oos) == ["generation: did not abstain on out-of-scope question"]
    assert metrics.failure_stage({"id": "e", "error": "boom"}) == "error"


def test_aggregate_skips_not_applicable_values():
    rs = [
        _result(),
        _result(act_hit=False, fact_hit=0.0, judge={"faithfulness": 0.5, "relevance": 0.5, "reference_coverage": 0.0, "unsupported_claims": ["a", "b"]}),
        _result(category="out_of_scope", act_hit=None, fact_hit=None,
                judge={"faithfulness": 0.0, "relevance": 1.0, "reference_coverage": 1.0, "unsupported_claims": [], "abstained_correctly": True}),
        {"id": "err", "category": "answerable", "error": "boom"},
    ]
    agg = metrics.aggregate(rs)
    assert agg["n"] == 4
    assert agg["completion_rate"] == 0.75
    assert agg["act_hit_rate"] == 0.5
    assert agg["fact_hit"] == 0.5
    assert agg["faithfulness"] == 0.75  # out_of_scope excluded from faithfulness
    assert agg["abstention_rate"] == 1.0
    assert agg["mean_unsupported_claims"] == round(2 / 3, 4)
    assert agg["pass_rate"] == 0.5
    by_cat = metrics.aggregate_by_category(rs)
    assert set(by_cat) == {"answerable", "out_of_scope"}
    assert by_cat["out_of_scope"]["act_hit_rate"] is None


def test_compare_to_baseline_tolerance():
    base = {"fact_hit": 0.80, "faithfulness": 0.90, "relevance": 0.5, "act_hit_rate": None}
    cur = {"fact_hit": 0.74, "faithfulness": 0.85, "relevance": 0.9, "act_hit_rate": 1.0}
    rows = {r["metric"]: r for r in metrics.compare_to_baseline(cur, base)}
    assert rows["fact_hit"]["regressed"] is True       # dropped 0.06
    assert rows["faithfulness"]["regressed"] is False  # dropped exactly 0.05
    assert rows["relevance"]["regressed"] is False     # improved
    assert rows["act_hit_rate"]["delta"] is None       # missing in baseline
