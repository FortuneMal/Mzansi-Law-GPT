"""Runs the golden question set through the live RAG pipeline and scores it.

Usage (from the repository root):
    python evals/run_evals.py [--limit N] [--category CAT] [--collection NAME]
                              [--force-local] [--out DIR] [--baseline PATH]

Retrieval and generation go through rag_core.retrieve_sources and
rag_core.generate_answer, the same functions used by /api/chat and
/api/chat/stream. See evals/README.md for metric definitions.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime

EVALS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(EVALS_DIR)
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, EVALS_DIR)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(REPO_ROOT, ".env"))

import metrics  # noqa: E402

JUDGE_MODEL = "gpt-4o-mini"
DEFAULT_GOLDEN = os.path.join(EVALS_DIR, "golden_set.jsonl")
DEFAULT_OUT = os.path.join(EVALS_DIR, "results")

JUDGE_SYSTEM_PROMPT = """You are a strict evaluator of a South African legal question-answering system.
Grade ONLY against the RETRIEVED CONTEXT supplied to you. Do not use your own legal knowledge to decide whether a claim is supported: a claim that may be true in law but is not stated in the retrieved context is unsupported.

Work in two steps. First, list every substantive legal claim in the ANSWER: each statement of a legal rule, right, duty, time period, amount, penalty, procedure, or attribution of content to a named Act, section, regulation or case. Generic disclaimers, advice to consult an attorney or check SAFLII, restating the question, and formatting are not claims. For each claim decide whether the RETRIEVED CONTEXT states it (paraphrase is fine; a claim that attributes content to an Act or section is supported only if that Act's text in the context says it).

Then return a JSON object with exactly these keys:
- "claims": list of objects {"claim": short string, "supported": true or false}, one per substantive legal claim. Empty list if there are none.
- "relevance": number from 0 to 1. How directly and completely the ANSWER addresses the QUESTION that was asked.
- "reference_coverage": number from 0 to 1. The fraction of REFERENCE POINTS that the ANSWER correctly conveys.
- "states_not_covered": true if the ANSWER explicitly tells the user that the retrieved sources or provided context do not cover the question, or do not contain the specific information requested; otherwise false. A generic closing disclaimer, or a remark that only one cited Act is "not in the context", does not count.
- "rationale": one or two sentences explaining the scores."""

JUDGE_USER_TEMPLATE = """CATEGORY: {category}

QUESTION:
{question}

REFERENCE POINTS:
{reference_points}

RETRIEVED CONTEXT:
{context}

ANSWER:
{answer}"""


def _clamp01(v):
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return None


def judge_answer(client, item: dict, context: str, answer: str) -> dict:
    """LLM-as-judge scores for one answer. Never raises; failures are returned under "error"."""
    try:
        completion = client.chat.completions.create(
            model=JUDGE_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": JUDGE_USER_TEMPLATE.format(
                    category=item["category"],
                    question=item["question"],
                    reference_points="\n".join(f"- {p}" for p in item.get("reference_points", [])),
                    context=context,
                    answer=answer,
                )},
            ],
        )
        raw = json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    claims = raw.get("claims")
    if not isinstance(claims, list):
        return {"error": "judge response missing 'claims' list", "raw": raw}
    claims = [c for c in claims if isinstance(c, dict)]
    unsupported = [str(c.get("claim", "")) for c in claims if c.get("supported") is not True]
    states_not_covered = raw.get("states_not_covered")
    states_not_covered = states_not_covered if isinstance(states_not_covered, bool) else None
    # Derived, not asked of the judge directly: a correct abstention says the sources do not cover the
    # question AND makes no unsupported legal claims. (A direct boolean proved inconsistent with the
    # judge's own rationale in early runs.)
    abstained = None
    if item["category"] == "out_of_scope" and states_not_covered is not None:
        abstained = states_not_covered and not unsupported
    return {
        # Faithfulness is computed from the claim list rather than trusting a free-form score.
        "faithfulness": round((len(claims) - len(unsupported)) / len(claims), 4) if claims else 1.0,
        "relevance": _clamp01(raw.get("relevance")),
        "reference_coverage": _clamp01(raw.get("reference_coverage")),
        "claims_total": len(claims),
        "unsupported_claims": unsupported,
        "states_not_covered": states_not_covered,
        "abstained_correctly": abstained,
        "rationale": str(raw.get("rationale", "")),
    }


def load_golden(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _git_revision() -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        return rev + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def _backend_of(vector_store) -> str:
    inner = type(getattr(vector_store.client, "_client", None)).__name__
    return {"QdrantRemote": "cloud", "QdrantLocal": "local"}.get(inner, inner)


def evaluate_item(item: dict, args, client) -> dict:
    from rag_core import ChatRequest, generate_answer, retrieve_sources

    result = {"id": item["id"], "category": item["category"], "question": item["question"]}
    try:
        t0 = time.perf_counter()
        req = ChatRequest(query=item["question"], collection_name=args.collection, force_local=args.force_local)
        sources, context, messages_payload = retrieve_sources(req)
        t1 = time.perf_counter()
        answer = generate_answer(messages_payload, client)
        t2 = time.perf_counter()
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        return result

    src_dicts = [s.model_dump() for s in sources]
    retrieved_acts = [s["act"] for s in src_dicts]
    result.update({
        "retrieved": [{"act": s["act"], "section": s["section"], "source_file": s["source_file"]} for s in src_dicts],
        "context": context,
        "answer": answer,
        "act_hit": metrics.act_hit(item["expected_acts"], retrieved_acts),
        "act_recall": metrics.act_recall(item["expected_acts"], retrieved_acts),
        "fact_hit": metrics.fact_hit(item["expected_facts"], context),
        "missing_facts": metrics.missing_facts(item["expected_facts"], context),
        "citation": metrics.citation_check(answer, src_dicts, context),
        "retrieval_ms": round((t1 - t0) * 1000, 1),
        "latency_ms": round((t2 - t0) * 1000, 1),
    })
    result["judge"] = judge_answer(client, item, context, answer)
    return result


def _fmt(v) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


SUMMARY_METRICS = [
    "n", "pass_rate", "completion_rate", "act_hit_rate", "act_recall", "fact_hit", "citation_clean_rate",
    "faithfulness", "relevance", "reference_coverage", "abstention_rate", "mean_unsupported_claims", "mean_latency_ms",
]


def render_markdown(report: dict, comparison=None) -> str:
    meta, agg, by_cat = report["meta"], report["aggregate"], report["by_category"]
    k = meta["retrieval_k"]
    lines = [
        f"# Evaluation run {meta['run_id']}",
        "",
        f"- Git revision: `{meta['git_revision']}`",
        f"- Collection: `{meta['collection']}` ({meta['backend']}, {meta['collection_points']} points)",
        f"- Chat model: `{meta['chat_model']}`; judge model: `{meta['judge_model']}`; retrieval k = {k}",
        f"- Questions: {agg['n']} (golden set sha256 `{meta['golden_set_sha256'][:12]}`; filters: category={meta['category_filter']}, limit={meta['limit']})",
        "",
        "Retrieval metrics are computed at k = %d. The judge is uncalibrated; treat its scores as relative signals." % k,
        "",
        "## Aggregate metrics",
        "",
        "| Metric | Overall | " + " | ".join(by_cat.keys()) + " |",
        "|---|---|" + "---|" * len(by_cat),
    ]
    for m in SUMMARY_METRICS:
        lines.append(f"| {m} | {_fmt(agg.get(m))} | " + " | ".join(_fmt(c.get(m)) for c in by_cat.values()) + " |")

    if comparison is not None:
        lines += ["", f"## Comparison with baseline (`{comparison['path']}`)", "",
                  "| Metric | Baseline | Current | Delta | Regressed |", "|---|---|---|---|---|"]
        for row in comparison["rows"]:
            lines.append(f"| {row['metric']} | {_fmt(row['baseline'])} | {_fmt(row['current'])} | {_fmt(row['delta'])} | {'YES' if row['regressed'] else ''} |")
        if comparison.get("warning"):
            lines += ["", f"Warning: {comparison['warning']}"]

    failing = [r for r in report["results"] if metrics.failure_reasons(r)]
    lines += ["", f"## Failing questions ({len(failing)} of {agg['n']})", ""]
    if failing:
        lines += ["| ID | Category | Stage | Retrieved Acts | Reasons |", "|---|---|---|---|---|"]
        for r in failing:
            acts = ", ".join(sorted({x["act"] for x in r.get("retrieved", [])})) or "-"
            reasons = "<br>".join(metrics.failure_reasons(r)).replace("|", "\\|")
            lines.append(f"| {r['id']} | {r['category']} | {metrics.failure_stage(r)} | {acts} | {reasons} |")
    else:
        lines.append("None.")

    lines += ["", "## Unsupported claims reported by the judge", ""]
    any_claims = False
    for r in report["results"]:
        claims = (r.get("judge") or {}).get("unsupported_claims") or []
        if claims:
            any_claims = True
            lines.append(f"- **{r['id']}**: " + "; ".join(c.replace("\n", " ") for c in claims))
    if not any_claims:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the Mzansi Law GPT RAG pipeline against the golden set.")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate at most N questions (after --category filtering)")
    parser.add_argument("--collection", default=None, help="Qdrant collection (default: the API default, mzansi_law_acts_v2)")
    parser.add_argument("--force-local", action="store_true", help="Use the local qdrant_db store instead of Qdrant Cloud")
    parser.add_argument("--category", default=None, help="Only evaluate one category (answerable, multi_act, out_of_scope, adversarial)")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output directory for <timestamp>.json and .md (default: evals/results)")
    parser.add_argument("--baseline", default=None, help="Baseline results JSON; exit non-zero if any gated metric drops by more than 0.05")
    parser.add_argument("--golden", default=DEFAULT_GOLDEN, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    from rag_core import CHAT_MODEL, DEFAULT_COLLECTION, RETRIEVAL_K, get_openai_client
    from contract_review import get_qdrant_vector_store

    args.collection = args.collection or DEFAULT_COLLECTION

    missing = [v for v in ["OPENAI_API_KEY"] if not os.getenv(v)]
    if not args.force_local:
        missing += [v for v in ["QDRANT_URL", "QDRANT_API_KEY"] if not os.getenv(v)]
    if missing:
        print(f"[ERROR] Missing credentials: {', '.join(missing)}. Set them in .env; the eval will not run against mocks.", file=sys.stderr)
        return 2

    items = load_golden(args.golden)
    if args.category:
        items = [i for i in items if i["category"] == args.category]
    if args.limit is not None:
        items = items[: args.limit]
    if not items:
        print("[ERROR] No questions selected.", file=sys.stderr)
        return 2

    # get_qdrant_vector_store silently falls back to the local store; refuse to evaluate the wrong corpus.
    try:
        vector_store = get_qdrant_vector_store(collection_name=args.collection, force_local=args.force_local)
        backend = _backend_of(vector_store)
        points = vector_store.client.count(args.collection).count
    except Exception as e:
        print(f"[ERROR] Could not open collection '{args.collection}': {e}", file=sys.stderr)
        return 2
    if not args.force_local and backend != "cloud":
        print(f"[ERROR] Qdrant Cloud collection '{args.collection}' was not reachable; the store fell back to '{backend}'. "
              "Fix the cloud connection or pass --force-local to evaluate the local store deliberately.", file=sys.stderr)
        return 2

    client = get_openai_client()
    with open(args.golden, "rb") as f:
        golden_sha = hashlib.sha256(f.read()).hexdigest()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"Evaluating {len(items)} questions against '{args.collection}' ({backend}, {points} points)...")

    results = []
    for n, item in enumerate(items, 1):
        r = evaluate_item(item, args, client)
        results.append(r)
        status = "PASS" if not metrics.failure_reasons(r) else "FAIL"
        print(f"[{n:>2}/{len(items)}] {status} {item['id']}")

    report = {
        "meta": {
            "run_id": run_id,
            "git_revision": _git_revision(),
            "collection": args.collection,
            "backend": backend,
            "collection_points": points,
            "chat_model": CHAT_MODEL,
            "judge_model": JUDGE_MODEL,
            "retrieval_k": RETRIEVAL_K,
            "golden_set_sha256": golden_sha,
            "category_filter": args.category,
            "limit": args.limit,
        },
        "aggregate": metrics.aggregate(results),
        "by_category": metrics.aggregate_by_category(results),
        "results": results,
    }

    comparison, exit_code = None, 0
    if args.baseline:
        with open(args.baseline, encoding="utf-8") as f:
            base = json.load(f)
        rows = metrics.compare_to_baseline(report["aggregate"], base["aggregate"])
        comparison = {"path": args.baseline, "rows": rows}
        base_ids = {r["id"] for r in base.get("results", [])}
        if base_ids != {r["id"] for r in results}:
            comparison["warning"] = "question sets differ from the baseline run; deltas are not like-for-like."
        report["baseline_comparison"] = comparison
        if any(r["regressed"] for r in rows):
            exit_code = 1

    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, f"{run_id}.json")
    md_path = os.path.join(args.out, f"{run_id}.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(report, comparison))

    agg = report["aggregate"]
    print("\n" + " ".join(f"{m}={_fmt(agg.get(m))}" for m in SUMMARY_METRICS))
    print(f"Wrote {json_path}\nWrote {md_path}")
    if comparison is not None:
        for row in comparison["rows"]:
            if row["regressed"]:
                print(f"[REGRESSION] {row['metric']}: {row['baseline']} -> {row['current']}", file=sys.stderr)
        if comparison.get("warning"):
            print(f"[WARN] {comparison['warning']}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
