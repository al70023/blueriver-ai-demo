# Evals

A small retrieval and Q&A eval harness for the BlueRiver AI Review Desk.

## Why this exists

A RAG demo is easy to ship. A RAG demo that doesn't silently regress when you change the chunker, the embedding model, or the retrieval logic is harder. This directory exists to make it boring to verify that retrieval and answer quality stay where they should be.

The eval set is small on purpose. 20 questions across 4 sample documents. The point is to have something runnable in under a minute that catches the obvious regressions, not to produce a research paper.

## What it measures

For each question in `eval_set.json` the harness checks two things:

1. **Retrieval quality** — did the top-K retrieved chunks contain the expected keywords? Pass if every keyword appears in at least one retrieved chunk's text.
2. **Answer quality** — did the LLM's final answer contain the expected keywords? Pass if every keyword appears in the answer (case-insensitive).

These are intentionally crude metrics. They will not tell you whether an answer is *good*, only whether it has the right facts in it. Every keyword in the eval set was chosen so that any reasonable correct answer would naturally contain it. If you find one that's tripping things up unfairly, edit the eval — it's just JSON.

The harness does not use exact chunk-ID matching because chunk IDs are not stable across re-ingestion (they depend on insertion order and the chunker's behavior). Matching by keyword survives re-indexing.

## How to run it

```bash
# 1. Install the eval script dependency in the Python environment
# you're using from this shell.
cd evals
python -m pip install -r requirements.txt

# 2. Make sure the backend is up and the four sample documents are uploaded.
python upload_samples.py

# 3. Run the eval.
python run_evals.py
```

Output looks like:

```
  [policy-coverage-amounts]  retrieval: PASS   answer: PASS   (612 ms)
  [policy-aggregate-limit]   retrieval: PASS   answer: PASS   (487 ms)
  ...

============================================================
Summary
============================================================
  total questions:      20
  retrieval pass rate:  18/20 (90.0%)
  answer pass rate:     17/20 (85.0%)
  avg latency:          640 ms

By category:
  action_extraction               retrieval 5/6    answer 4/6
  cross_document_reasoning        retrieval 1/1    answer 1/1
  factual_lookup                  retrieval 12/13  answer 12/13

Detailed results written to results.json
```

## Baseline

Last known baseline on the included sample corpus:

| Metric | Value |
|---|---|
| Retrieval pass rate | 19/20 (95.0%) |
| Answer pass rate | 15/20 (75.0%) on strict keyword match |
| Manual answer spot-check | 20/20 factually correct |
| Median latency | 4,453 ms |
| Mean latency | 5,153 ms |
| Model | gpt-4.1-mini |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |

The answer score is intentionally conservative because the harness uses exact keyword matching. In this run, all five answer failures were paraphrase or morphology mismatches rather than factual errors: `14-day` vs. `14 days`, `replacement` vs. `replace`, and `recalibration` vs. `recalibrate`, for example. A semantic-equivalence eval using an LLM judge or embedding similarity would measure answer quality more accurately and belongs in a future version.

The one retrieval miss was `policy-banking-verification`: the answer correctly included "Email confirmation alone is not acceptable," but the strict retrieval check did not find the exact `Email confirmation` keyword in the returned citation text.

Strict keyword misses from this baseline:

| Eval item | Retrieval | Answer | Missing keywords |
|---|---:|---:|---|
| policy-additional-insured | PASS | FAIL | `General Liability` |
| policy-tier-thresholds | PASS | FAIL | `Tier 3` |
| policy-emergency-window | PASS | FAIL | `14-day` |
| policy-banking-verification | FAIL | PASS | `Email confirmation` in retrieved chunks |
| service-report-contactor | PASS | FAIL | `replacement` |
| service-report-economizer | PASS | FAIL | `drift`, `recalibration` |

## What this is not

- Not a hallucination detector. The harness only checks that expected keywords appear; it does not check that *unexpected* claims are absent.
- Not a substitute for human review on real client documents. Replace `eval_set.json` with questions written against your own corpus before claiming any quality bar to a paying client.
- Not a substitute for production monitoring. For that, swap to Langfuse or Phoenix and trace real user queries.

## Wiring this into CI

The harness exits non-zero if retrieval or answer pass rate drops below 50%. To run it in CI you need a running backend with the samples uploaded and an `OPENAI_API_KEY` available. A minimal GitHub Actions step:

```yaml
- name: Run eval harness
  run: |
    python evals/upload_samples.py --api-base http://localhost:8000
    python evals/run_evals.py --api-base http://localhost:8000
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

For now this is documented but not wired in — it's a v2 nice-to-have.
