"""
BlueRiver eval harness.

Runs the questions in eval_set.json against a running BlueRiver backend
and reports retrieval and answer quality. Designed to be simple enough
to read in one sitting.

Usage:
    1. Start the backend (see project README).
    2. Upload the four sample documents from /samples via the UI or via
       the upload script in this directory:
           python upload_samples.py
    3. Run:
           python run_evals.py
       or with a custom API base URL:
           python run_evals.py --api-base http://localhost:8000

The harness checks two things per question:

  1. Retrieval quality — did the top-K retrieved chunks contain the
     expected keywords from the eval item? (Pass if all keywords appear
     in at least one retrieved chunk.)

  2. Answer quality — did the LLM's answer contain the expected
     keywords? (Pass if all keywords appear, case-insensitive.)

These are intentionally simple metrics. They are not a substitute for
human review, but they catch regressions: if you change the chunker,
the embedding model, or the retrieval logic and the eval pass rate
drops, you know something broke.

Output is printed to stdout and also written to results.json so you can
diff results across runs.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NotRequired, TypeAlias, TypedDict, Union, cast

import requests


JsonValue: TypeAlias = Union[
    None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]
]


class DocumentSummary(TypedDict):
    id: int
    filename: str


class EvalItem(TypedDict):
    id: str
    question: str
    expected_document: str
    expected_keywords: list[str]
    category: NotRequired[str]


class EvalSet(TypedDict):
    documents: list[str]
    items: list[EvalItem]
    version: NotRequired[str]
    description: NotRequired[str]


class CitationResponse(TypedDict):
    text: str


class AskResponseJson(TypedDict, total=False):
    answer: str
    citations: list[CitationResponse]


@dataclass
class ItemResult:
    id: str
    question: str
    category: str
    retrieval_pass: bool
    answer_pass: bool
    missing_in_retrieval: list[str]
    missing_in_answer: list[str]
    answer_text: str
    citation_count: int
    latency_ms: int


def find_document_id(api_base: str, expected_filename: str) -> int | None:
    """Look up a document ID by filename. Returns None if not found."""
    response = requests.get(f"{api_base}/documents", timeout=10)
    response.raise_for_status()
    documents = cast("list[DocumentSummary]", response.json())
    for doc in documents:
        filename = doc["filename"]
        if filename == expected_filename:
            return doc["id"]
        # sample files may be uploaded as .pdf even though the source is .txt;
        # match on stem too
        if Path(filename).stem == Path(expected_filename).stem:
            return doc["id"]
    return None


def keywords_present(haystack: str, keywords: list[str]) -> tuple[bool, list[str]]:
    """Check that every keyword appears in the haystack (case-insensitive).
    Returns (all_present, missing_keywords)."""
    haystack_lower = haystack.lower()
    missing = [kw for kw in keywords if kw.lower() not in haystack_lower]
    return (len(missing) == 0, missing)


def evaluate_item(
    api_base: str, item: EvalItem, doc_lookup: dict[str, int]
) -> ItemResult:
    """Run one eval item: ask the question, check retrieval and answer."""
    expected_doc = item["expected_document"]
    document_id: int | None = None
    if expected_doc and expected_doc != "any":
        document_id = doc_lookup.get(expected_doc)

    payload: dict[str, JsonValue] = {"question": item["question"], "limit": 5}
    if document_id is not None:
        payload["document_id"] = document_id

    start = time.perf_counter()
    response = requests.post(f"{api_base}/ask", json=payload, timeout=60)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    response.raise_for_status()
    data = cast(AskResponseJson, response.json())

    answer_text = data.get("answer", "") or ""
    citations: list[CitationResponse] = data.get("citations", []) or []
    retrieved_text = " ".join(c.get("text", "") for c in citations)

    expected_keywords = item["expected_keywords"]
    retrieval_ok, missing_retrieval = keywords_present(
        retrieved_text, expected_keywords
    )
    answer_ok, missing_answer = keywords_present(answer_text, expected_keywords)

    return ItemResult(
        id=item["id"],
        question=item["question"],
        category=item.get("category", "uncategorized"),
        retrieval_pass=retrieval_ok,
        answer_pass=answer_ok,
        missing_in_retrieval=missing_retrieval,
        missing_in_answer=missing_answer,
        answer_text=answer_text,
        citation_count=len(citations),
        latency_ms=elapsed_ms,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="BlueRiver eval harness.")
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="Base URL of the BlueRiver backend.",
    )
    parser.add_argument(
        "--eval-file", default="eval_set.json", help="Path to the eval JSON file."
    )
    parser.add_argument(
        "--results-file",
        default="results.json",
        help="Where to write detailed results.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-item output, show summary only.",
    )
    args = parser.parse_args()

    eval_path = Path(args.eval_file)
    if not eval_path.exists():
        print(f"ERROR: eval file not found: {eval_path}", file=sys.stderr)
        return 2

    with eval_path.open() as f:
        eval_data = cast(EvalSet, json.load(f))

    items = eval_data["items"]
    expected_docs = set(eval_data["documents"])

    # health check
    try:
        health = cast(
            "dict[str, str]",
            requests.get(f"{args.api_base}/health", timeout=5).json(),
        )
    except Exception as e:
        print(f"ERROR: cannot reach backend at {args.api_base}: {e}", file=sys.stderr)
        return 2
    if any(v != "ok" for v in health.values()):
        print(f"ERROR: backend health check failed: {health}", file=sys.stderr)
        return 2

    # build a filename -> document_id lookup
    doc_lookup: dict[str, int] = {}
    for fname in expected_docs:
        doc_id = find_document_id(args.api_base, fname)
        if doc_id is not None:
            doc_lookup[fname] = doc_id

    missing_docs = expected_docs - set(doc_lookup.keys())
    if missing_docs:
        print("WARNING: the following expected documents are not uploaded:")
        for fname in missing_docs:
            print(f"  - {fname}")
        print("Items targeting these documents will likely fail retrieval.")
        print("Upload the samples first (see evals/README.md).\n")

    results: list[ItemResult] = []
    for item in items:
        try:
            result = evaluate_item(args.api_base, item, doc_lookup)
        except Exception as e:
            print(f"  [{item['id']}] ERROR: {e}")
            continue
        results.append(result)
        if not args.quiet:
            r_mark = "PASS" if result.retrieval_pass else "FAIL"
            a_mark = "PASS" if result.answer_pass else "FAIL"
            print(
                f"  [{result.id}]  retrieval: {r_mark}   answer: {a_mark}   "
                f"({result.latency_ms} ms)"
            )
            if not result.retrieval_pass:
                print(
                    f"      missing in retrieved chunks: {result.missing_in_retrieval}"
                )
            if not result.answer_pass:
                print(f"      missing in answer: {result.missing_in_answer}")

    # summary
    total = len(results)
    if total == 0:
        print("No results.")
        return 1

    retrieval_passes = sum(1 for r in results if r.retrieval_pass)
    answer_passes = sum(1 for r in results if r.answer_pass)
    avg_latency = sum(r.latency_ms for r in results) / total

    by_category: dict[str, dict[str, int]] = {}
    for r in results:
        cat = by_category.setdefault(
            r.category, {"total": 0, "retrieval": 0, "answer": 0}
        )
        cat["total"] += 1
        cat["retrieval"] += int(r.retrieval_pass)
        cat["answer"] += int(r.answer_pass)

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  total questions:      {total}")
    print(
        f"  retrieval pass rate:  {retrieval_passes}/{total} "
        f"({100 * retrieval_passes / total:.1f}%)"
    )
    print(
        f"  answer pass rate:     {answer_passes}/{total} "
        f"({100 * answer_passes / total:.1f}%)"
    )
    print(f"  avg latency:          {avg_latency:.0f} ms")
    print()
    print("By category:")
    for cat, counts in sorted(by_category.items()):
        print(
            f"  {cat:30s}  retrieval {counts['retrieval']}/{counts['total']:<3d}  "
            f"answer {counts['answer']}/{counts['total']}"
        )

    out_path = Path(args.results_file)
    out_path.write_text(json.dumps([asdict(r) for r in results], indent=2))
    print()
    print(f"Detailed results written to {out_path}")

    # exit non-zero if either pass rate is below 50%, so this can be wired
    # into CI later
    threshold = 0.5
    if (retrieval_passes / total) < threshold or (answer_passes / total) < threshold:
        print(f"\nWARNING: pass rate below threshold ({threshold * 100:.0f}%).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
