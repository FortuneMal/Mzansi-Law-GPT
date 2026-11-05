# Evaluation harness

> **Legal review required.** The questions, expected facts and reference points in
> `golden_set.jsonl` were drafted from the text in `data/raw_acts/` by an engineer and
> an AI assistant, not by a lawyer. A person qualified in South African law must check
> each item for legal accuracy and then set its `"reviewed"` field to `true`. Until
> then, treat the scores as measuring agreement with the corpus text, not legal correctness.

This directory contains a repeatable evaluation of the chat RAG pipeline. It runs a fixed
set of questions through the same retrieval and generation code the API uses
(`rag_core.retrieve_sources` and `rag_core.generate_answer`), then scores retrieval,
citations and answer quality.

## Files

| Path | Purpose |
|---|---|
| `golden_set.jsonl` | The question set, one JSON object per line. |
| `run_evals.py` | Runner: executes the questions, calls the LLM judge, writes reports. |
| `metrics.py` | Deterministic metric functions (no network). |
| `baseline.json` | The committed reference run used for regression checks. |
| `results/` | Output of each run (`<timestamp>.json` and `<timestamp>.md`). Not committed. |

## Running

Run from the repository root with the project virtual environment active. The runner reads
`OPENAI_API_KEY`, `QDRANT_URL` and `QDRANT_API_KEY` from `.env` and stops if any is missing.

```bash
pip install -r requirements-dev.txt

python evals/run_evals.py --limit 5                       # quick smoke run
python evals/run_evals.py                                 # full run
python evals/run_evals.py --category out_of_scope         # one category
python evals/run_evals.py --baseline evals/baseline.json  # regression check
```

| Option | Meaning |
|---|---|
| `--limit N` | Evaluate at most N questions, after any category filter. |
| `--category CAT` | `answerable`, `multi_act`, `out_of_scope` or `adversarial`. |
| `--collection NAME` | Qdrant collection. Defaults to the API default, `mzansi_law_acts_v2`. |
| `--force-local` | Use the local `qdrant_db` store instead of Qdrant Cloud. |
| `--out DIR` | Output directory. Defaults to `evals/results`. |
| `--baseline PATH` | Compare aggregate metrics with a previous run and exit with status 1 if any gated metric drops by more than 0.05. |

`get_qdrant_vector_store` silently falls back to the local store when the cloud collection is
unreachable. The runner refuses to continue in that case unless `--force-local` is given, so a
run is never scored against the wrong corpus by accident. The local `qdrant_db` currently holds
only the legacy `mzansi_law_acts` collection, so `--force-local` with the default collection
will fail until the corpus is ingested locally.

A full run of 30 questions takes about four minutes and makes roughly 90 OpenAI calls
(embedding, answer and judge per question).

To refresh the baseline after an intended change, run the full set and copy the resulting
JSON file to `evals/baseline.json`.

Unit tests for the metrics, the query logger and the endpoint logging live in `tests/` and run
without network access:

```bash
python -m pytest
```

## Golden set format

Each line has these fields:

| Field | Meaning |
|---|---|
| `id` | Stable identifier. |
| `category` | `answerable` (18), `multi_act` (5), `out_of_scope` (5), `adversarial` (2). |
| `question` | The user query, sent with `act_filter` "All Acts" and no history. |
| `expected_acts` | Act titles exactly as they appear in retrieval metadata (`metadata.act`). |
| `expected_facts` | Short phrases copied from the corpus that a correct retrieval must contain. |
| `reference_points` | What a correct answer must state, used by the judge. |
| `reviewed` | `false` until a legal reviewer has checked the item. |

`tests/test_golden_set.py` checks that every expected Act title exists, and that every expected
fact appears in a chunk of one of its expected Acts as produced by `data_ingestion.py`.

Out-of-scope questions cover topics the corpus does not contain (divorce, eviction, drunk
driving, wills) and one question whose Act is indexed but whose specific detail (the rand amount
of the minimum wage) is not. The correct behaviour is to say the sources do not cover it and
point the user to SAFLII or an attorney. Adversarial questions contain a false premise that a
correct answer must correct.

## Metrics

Retrieval uses k = 4, the value hard-coded in the API. Act matching is done at Act level only,
because section metadata falls back to `Chunk_N` when no section number is detected and is
otherwise taken from the first section-like token in a chunk.

| Metric | Definition | Applies to |
|---|---|---|
| `act_hit_rate` (act_hit@4) | Share of questions where at least one expected Act is among the retrieved sources. | Questions with `expected_acts`. |
| `act_recall` | Mean fraction of expected Acts retrieved. Distinguishes partial retrieval on multi-Act questions. | Questions with `expected_acts`. |
| `fact_hit` (fact_hit@4) | Mean fraction of `expected_facts` found in the retrieved context. Matching lowercases, folds unicode, replaces punctuation with spaces and requires word boundaries. | Questions with `expected_facts`. |
| `citation_clean_rate` | Share of answers with no unsupported citations (see below). | All. |
| `faithfulness` | Judge: supported claims divided by all substantive legal claims in the answer. 1.0 when the answer makes no claims. | All except `out_of_scope`. |
| `relevance` | Judge: 0 to 1, how directly the answer addresses the question. | All except `out_of_scope`. |
| `reference_coverage` | Judge: 0 to 1, fraction of `reference_points` the answer conveys. | All except `out_of_scope`. |
| `abstention_rate` | Share of out-of-scope answers that abstained correctly (see below). | `out_of_scope`. |
| `mean_unsupported_claims` | Mean number of claims the judge marked unsupported. | All. |
| `completion_rate` | Share of questions that ran without an exception. | All. |
| `pass_rate` | Share of questions with no failure reason. Not gated. | All. |

### Citation check

`metrics.extract_act_mentions` finds Acts named in a piece of text: known Act names and
abbreviations from the corpus (for example "Basic Conditions of Employment Act", "BCEA",
"Act 75 of 1997"), plus any other capitalised "... Act" name, which is reported as
`other:<name>`. For each answer:

- `cited_not_retrieved` lists Acts named in the answer that are not among the retrieved sources.
- `unsupported` is the subset that is also not named anywhere in the retrieved text. An Act that
  a retrieved chunk itself refers to (the LRA chunk cites "section 23 of the Constitution") is
  treated as supported.

An answer is citation-clean when `unsupported` is empty. Both lists are stored in the results.

### LLM judge

The judge is `gpt-4o-mini` at temperature 0 in JSON mode, using `OPENAI_API_KEY`. It receives
the category, question, reference points, retrieved context and answer. It is told to grade only
against the retrieved context, not its own legal knowledge. It returns:

- `claims`: every substantive legal claim in the answer, each with a `supported` flag.
  `faithfulness` and `unsupported_claims` are computed from this list.
- `relevance` and `reference_coverage` as 0 to 1 scores.
- `states_not_covered`: whether the answer explicitly says the sources do not cover the question.

`abstained_correctly` is then derived in code: `states_not_covered` is true **and** there are
no unsupported claims. An answer that says "the context does not cover this" and then gives
detailed rules from outside the corpus does not count as an abstention.

The scores come from the judge's verdicts; they are not asked for directly. The first version of
the judge asked for a single faithfulness number and a direct abstention boolean. It scored
faithfulness at 1.0 on every in-scope question, including one where the answer quoted a
Constitution section that had not been retrieved. It also returned `abstained_correctly: true`
in cases where its own rationale said the answer failed to abstain. The claim-level design
replaced it before the baseline was recorded.

### Failure attribution

The Markdown report lists every failing question with its reasons and a coarse stage:

- `retrieval`: an expected Act or fact was not retrieved.
- `generation`: retrieval was adequate but the answer fell below a threshold (faithfulness,
  relevance or reference coverage under 0.7), cited unsupported Acts, or failed to abstain.
- `error`: the pipeline raised an exception.

Out-of-scope failures are attributed to generation, because missing corpus content is the
premise of those questions and the expected behaviour is to abstain.

### Regression gate

`--baseline` compares the overall aggregates for `completion_rate`, `act_hit_rate`,
`act_recall`, `fact_hit`, `citation_clean_rate`, `faithfulness`, `relevance`,
`reference_coverage` and `abstention_rate`. It exits with status 1 if any of them is lower than
the baseline by more than 0.05. Per-category deltas are not gated, because the categories are
too small. If the question sets differ (for example because of `--limit`), the report warns that
the comparison is not like-for-like.

## Known limitations

- **Small corpus.** The indexed collection holds 35 chunks from 17 files, about 24 KB of text.
  Most files contain only one to seven sections of their Act. Many reasonable questions about an
  Act that is "covered" will have no grounding text. Scores say nothing about coverage of South
  African law in general.
- **Unreliable section metadata.** Section numbers fall back to `Chunk_N`, and a chunk containing
  several sections is labelled with the first section-like match. Retrieval is therefore scored
  at Act level only, and the harness does not check whether cited section numbers are correct.
- **Uncalibrated judge.** The judge is the same model family as the generator, has not been
  compared with human ratings, and can be lenient or inconsistent. Treat its scores as relative
  signals between runs on the same judge prompt. Do not read them as absolute quality, and do not
  compare runs made with different judge prompts. In two consecutive full runs with the same
  prompt, the judge-based aggregates moved by up to 0.011. Retrieval metrics did not change.
- **Non-deterministic generation.** Answers use temperature 0.2. Individual out-of-scope
  verdicts can flip between runs (the minimum-wage question has both passed and failed). With
  five out-of-scope questions, one flip moves `abstention_rate` by 0.2 and trips the gate.
- **Small categories.** Some categories have two to five questions, so per-category numbers are
  noisy.
- **Citation detection is heuristic.** It relies on capitalised "... Act" names and a list of
  known abbreviations. It can miss informal references, and it counts a pointer such as "see the
  Wills Act" as an unsupported citation even when no content is attributed to it.
- **Single-turn only.** Questions are sent without history and with `act_filter` "All Acts", so
  the act filter and multi-turn behaviour are not evaluated.

## Query logging

Separately from the evals, the API can log live traffic. Start it with `MZANSI_LOG_QUERIES=1` and
each `/api/chat` and `/api/chat/stream` request appends one JSON line to `logs/queries.jsonl`:
timestamp, endpoint, query, act filter, collection, retrieved sources (Act and section), answer,
model, latency in milliseconds, and error, if any. Streamed answers are accumulated and logged
once, after the final `done` or `error` event, or when the client disconnects. Logging failures
are swallowed and reported once on stderr. `query_log.log_rag_event` is the integration point for
a future external evaluation service. `logs/` is git-ignored.
