"""Deterministic evaluation metrics for the Mzansi Law GPT RAG pipeline.

Everything here is pure (no network, no model calls) so it can be unit tested.
Act matching works at Act level only: section metadata is unreliable because
ingestion falls back to "Chunk_N" when no section number is detected.
"""
import re
import unicodedata
from typing import Dict, Iterable, List, Optional, Set

# Thresholds used to flag a question as failing in the summary report.
FAITHFULNESS_MIN = 0.7
RELEVANCE_MIN = 0.7
COVERAGE_MIN = 0.7

# Aggregate metrics compared against a baseline. All are "higher is better".
GATED_METRICS = [
    "completion_rate",
    "act_hit_rate",
    "act_recall",
    "fact_hit",
    "citation_clean_rate",
    "faithfulness",
    "relevance",
    "reference_coverage",
    "abstention_rate",
]
REGRESSION_TOLERANCE = 0.05


def normalise(text: str) -> str:
    """Lowercase, fold unicode, turn every non-alphanumeric run into one space."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def _contains(haystack_norm: str, needle: str) -> bool:
    n = normalise(needle)
    if not n:
        return False
    return f" {n} " in f" {haystack_norm} "


# ---------------------------------------------------------------------------
# Retrieval metrics
# ---------------------------------------------------------------------------

def act_hit(expected_acts: List[str], retrieved_acts: Iterable[str]) -> Optional[bool]:
    """True if any expected Act title is among the retrieved source Acts. None when nothing is expected."""
    if not expected_acts:
        return None
    retrieved = {normalise(a) for a in retrieved_acts}
    return any(normalise(a) in retrieved for a in expected_acts)


def act_recall(expected_acts: List[str], retrieved_acts: Iterable[str]) -> Optional[float]:
    """Fraction of expected Act titles present among retrieved source Acts. None when nothing is expected."""
    if not expected_acts:
        return None
    retrieved = {normalise(a) for a in retrieved_acts}
    return sum(normalise(a) in retrieved for a in expected_acts) / len(expected_acts)


def fact_hit(expected_facts: List[str], context: str) -> Optional[float]:
    """Fraction of expected facts found (normalised, word-bounded substring) in the retrieved context."""
    if not expected_facts:
        return None
    ctx = normalise(context)
    return sum(_contains(ctx, f) for f in expected_facts) / len(expected_facts)


def missing_facts(expected_facts: List[str], context: str) -> List[str]:
    ctx = normalise(context)
    return [f for f in expected_facts if not _contains(ctx, f)]


# ---------------------------------------------------------------------------
# Citation check
# ---------------------------------------------------------------------------

# key -> full names (matched case-insensitively) and abbreviations (matched case-sensitively).
ACT_CATALOGUE: Dict[str, Dict[str, list]] = {
    "popia_regs": {"names": ["POPIA General Regulations", "Regulations relating to the Protection of Personal Information"], "abbr": []},
    "harassment_code": {"names": ["Code of Good Practice on the Prevention and Elimination of Harassment", "Code of Good Practice on Harassment"], "abbr": []},
    "ccma_rules": {"names": ["Rules for the Conduct of Proceedings before the CCMA", "CCMA Rules"], "abbr": []},
    "bcea": {"names": ["Basic Conditions of Employment Act"], "abbr": ["BCEA"], "num": ("75", "1997")},
    "lra": {"names": ["Labour Relations Act"], "abbr": ["LRA"], "num": ("66", "1995")},
    "popia": {"names": ["Protection of Personal Information Act"], "abbr": ["POPIA", "POPI Act"], "num": ("4", "2013")},
    "cpa": {"names": ["Consumer Protection Act"], "abbr": ["CPA"], "num": ("68", "2008")},
    "companies": {"names": ["Companies Act"], "abbr": [], "num": ("71", "2008")},
    "nca": {"names": ["National Credit Act"], "abbr": ["NCA"], "num": ("34", "2005")},
    "ohsa": {"names": ["Occupational Health and Safety Act"], "abbr": ["OHSA"], "num": ("85", "1993")},
    "nmwa": {"names": ["National Minimum Wage Act"], "abbr": ["NMWA"], "num": ("9", "2018")},
    "eea": {"names": ["Employment Equity Act"], "abbr": ["EEA"], "num": ("55", "1998")},
    "ecta": {"names": ["Electronic Communications and Transactions Act"], "abbr": ["ECTA", "ECT Act"], "num": ("25", "2002")},
    "ppa": {"names": ["Property Practitioners Act"], "abbr": ["PPA"], "num": ("22", "2019")},
    "constitution": {"names": ["Constitution of the Republic of South Africa"], "abbr": ["Constitution"], "num": ("108", "1996")},
    "case_concourt": {"names": ["Mahlangu v Minister of Labour"], "abbr": ["Mahlangu"]},
    "case_sca": {"names": ["AfriForum v University of the Free State"], "abbr": ["AfriForum"]},
}

# Indexed source files -> catalogue key (from data/raw_acts).
SOURCE_FILE_KEYS = {
    "bcea_act_75_of_1997.txt": "bcea",
    "case_law_concourt.txt": "case_concourt",
    "case_law_sca.txt": "case_sca",
    "ccma_rules.txt": "ccma_rules",
    "companies_act_71_of_2008.txt": "companies",
    "constitution_act_108_of_1996.txt": "constitution",
    "cpa_act_68_of_2008.txt": "cpa",
    "ecta_act_25_of_2002.txt": "ecta",
    "eea_act_55_of_1998.txt": "eea",
    "lra_act_66_of_1995.txt": "lra",
    "lra_harassment_code.txt": "harassment_code",
    "nca_act_34_of_2005.txt": "nca",
    "nmwa_act_9_of_2018.txt": "nmwa",
    "ohsa_act_85_of_1993.txt": "ohsa",
    "popia_act_4_of_2013.txt": "popia",
    "popia_regulations.txt": "popia_regs",
    "ppa_act_22_of_2019.txt": "ppa",
}

_NUM_TO_KEY = {tuple(v["num"]): k for k, v in ACT_CATALOGUE.items() if "num" in v}
_LEADING_STOPWORDS = {"the", "this", "that", "under", "in", "per", "see", "your", "our", "both", "each", "an", "a", "and", "of"}
_GENERIC_ACT_RE = re.compile(
    r"\b((?:[A-Z][A-Za-z'\-]+)(?:\s+(?:of|and|the|on|for|to|in|[A-Z][A-Za-z'\-]+))*\s+Act)\b"
    r"(?:,?\s*(?:No\.?\s*)?(\d+)\s+of\s+(\d{4})|,?\s*(\d{4}))?"
)


def extract_act_mentions(text: str) -> Set[str]:
    """Returns catalogue keys (and "other:<name>" for unknown Acts) mentioned in free text."""
    if not text:
        return set()
    found: Set[str] = set()
    masked = text
    patterns = []
    for key, entry in ACT_CATALOGUE.items():
        for name in entry["names"]:
            patterns.append((len(name), key, re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)))
        for abbr in entry["abbr"]:
            patterns.append((len(abbr), key, re.compile(r"\b" + re.escape(abbr) + r"\b")))
    # Longest first, masking matches, so "POPIA General Regulations" is not also counted as "POPIA".
    for _, key, pat in sorted(patterns, key=lambda p: -p[0]):
        if pat.search(masked):
            found.add(key)
            masked = pat.sub(lambda m: " " * len(m.group(0)), masked)

    # Number/year citations ("Act 75 of 1997") identify known Acts even under a different name.
    for num, year in re.findall(r"\bAct\s+(?:No\.?\s*)?(\d+)\s+of\s+(\d{4})", masked):
        if (num, year) in _NUM_TO_KEY:
            found.add(_NUM_TO_KEY[(num, year)])
    for m in _GENERIC_ACT_RE.finditer(masked):
        words = m.group(1).split()
        while words and words[0].lower() in _LEADING_STOPWORDS:
            words.pop(0)
        if len(words) < 2:  # just "Act", or "The Act"
            continue
        num, year = m.group(2), m.group(3)
        if num and (num, year) in _NUM_TO_KEY:
            found.add(_NUM_TO_KEY[(num, year)])
        else:
            found.add("other:" + normalise(" ".join(words)))
    return found


def source_key(act_title: str, source_file: str) -> str:
    """Maps a retrieved source to a catalogue key, preferring the source file name."""
    if source_file in SOURCE_FILE_KEYS:
        return SOURCE_FILE_KEYS[source_file]
    keys = extract_act_mentions(act_title.title()) | extract_act_mentions(act_title)
    known = sorted(k for k in keys if not k.startswith("other:"))
    return known[0] if known else "other:" + normalise(act_title)


def citation_check(answer: str, sources: List[dict], context: str) -> dict:
    """Flags Acts the answer mentions that are not backed by retrieval.

    cited_not_retrieved: mentioned Acts that are not among the retrieved source Acts (strict).
    unsupported: the subset that is also not named anywhere in the retrieved text. An Act that the
    retrieved text itself refers to (e.g. the LRA chunk citing "section 23 of the Constitution")
    is treated as supported.
    """
    mentioned = extract_act_mentions(answer)
    retrieved = {source_key(s.get("act", ""), s.get("source_file", "")) for s in sources}
    named_in_context = extract_act_mentions(context)
    cited_not_retrieved = sorted(mentioned - retrieved)
    unsupported = sorted(k for k in cited_not_retrieved if k not in named_in_context)
    return {
        "mentioned": sorted(mentioned),
        "retrieved": sorted(retrieved),
        "cited_not_retrieved": cited_not_retrieved,
        "unsupported": unsupported,
        "clean": not unsupported,
    }


# ---------------------------------------------------------------------------
# Per-question failure reasons, aggregation and baseline comparison
# ---------------------------------------------------------------------------

def failure_reasons(r: dict) -> List[str]:
    """Human-readable reasons a question result is considered failing. Empty list means pass."""
    reasons = []
    if r.get("error"):
        return [f"error: {r['error']}"]
    if r.get("act_hit") is False:
        reasons.append("retrieval: no expected Act retrieved")
    if r.get("fact_hit") is not None and r["fact_hit"] < 1.0:
        reasons.append("retrieval: missing facts " + "; ".join(r.get("missing_facts", [])))
    if r.get("citation", {}).get("unsupported"):
        reasons.append("citation: unsupported " + ", ".join(r["citation"]["unsupported"]))
    j = r.get("judge") or {}
    if j.get("error"):
        reasons.append(f"judge error: {j['error']}")
    if r.get("category") == "out_of_scope":
        if j.get("abstained_correctly") is False:
            reasons.append("generation: did not abstain on out-of-scope question")
    else:
        if j.get("faithfulness") is not None and j["faithfulness"] < FAITHFULNESS_MIN:
            reasons.append(f"generation: faithfulness {j['faithfulness']:.2f}")
        if j.get("relevance") is not None and j["relevance"] < RELEVANCE_MIN:
            reasons.append(f"generation: relevance {j['relevance']:.2f}")
        if j.get("reference_coverage") is not None and j["reference_coverage"] < COVERAGE_MIN:
            reasons.append(f"generation: reference coverage {j['reference_coverage']:.2f}")
    return reasons


def failure_stage(r: dict) -> str:
    """Coarse attribution of a failing result: error, retrieval, or generation."""
    reasons = failure_reasons(r)
    if not reasons:
        return "pass"
    if r.get("error"):
        return "error"
    if any(x.startswith("retrieval") for x in reasons):
        return "retrieval"
    return "generation"


def _mean(values: List[Optional[float]]) -> Optional[float]:
    vals = [float(v) for v in values if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def aggregate(results: List[dict]) -> dict:
    """Aggregate metrics over a list of per-question results. Metrics that do not apply are None."""
    ok = [r for r in results if not r.get("error")]
    judged = [r.get("judge") or {} for r in ok]
    non_oos = [r.get("judge") or {} for r in ok if r.get("category") != "out_of_scope"]
    return {
        "n": len(results),
        "completion_rate": round(len(ok) / len(results), 4) if results else None,
        "act_hit_rate": _mean([None if r.get("act_hit") is None else float(r["act_hit"]) for r in ok]),
        "act_recall": _mean([r.get("act_recall") for r in ok]),
        "fact_hit": _mean([r.get("fact_hit") for r in ok]),
        "citation_clean_rate": _mean([float(r["citation"]["clean"]) for r in ok if "citation" in r]),
        "faithfulness": _mean([j.get("faithfulness") for j in non_oos]),
        "relevance": _mean([j.get("relevance") for j in non_oos]),
        "reference_coverage": _mean([j.get("reference_coverage") for j in non_oos]),
        "abstention_rate": _mean([None if j.get("abstained_correctly") is None else float(j["abstained_correctly"]) for j in judged]),
        "mean_unsupported_claims": _mean([len(j["unsupported_claims"]) for j in judged if isinstance(j.get("unsupported_claims"), list)]),
        "pass_rate": round(sum(not failure_reasons(r) for r in results) / len(results), 4) if results else None,
        "mean_latency_ms": _mean([r.get("latency_ms") for r in ok]),
    }


def aggregate_by_category(results: List[dict]) -> Dict[str, dict]:
    cats: Dict[str, List[dict]] = {}
    for r in results:
        cats.setdefault(r.get("category", "unknown"), []).append(r)
    return {c: aggregate(rs) for c, rs in sorted(cats.items())}


def compare_to_baseline(current: dict, baseline: dict, tolerance: float = REGRESSION_TOLERANCE) -> List[dict]:
    """Returns one row per gated metric with the delta; rows with regressed=True dropped by more than tolerance."""
    rows = []
    for m in GATED_METRICS:
        cur, base = current.get(m), baseline.get(m)
        if cur is None or base is None:
            rows.append({"metric": m, "baseline": base, "current": cur, "delta": None, "regressed": False})
            continue
        delta = round(cur - base, 4)
        rows.append({"metric": m, "baseline": base, "current": cur, "delta": delta, "regressed": (base - cur) > tolerance + 1e-9})
    return rows
