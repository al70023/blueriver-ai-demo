"""
Upload all sample documents in /samples to a running BlueRiver backend.

Usage:
    python upload_samples.py
    python upload_samples.py --api-base http://localhost:8000
    python upload_samples.py --samples-dir ../samples

The backend's /documents/upload endpoint accepts multipart file uploads.
Files already present (matched by filename) are skipped.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload sample documents to BlueRiver."
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8000",
        help="Base URL of the BlueRiver backend.",
    )
    parser.add_argument(
        "--samples-dir", default="../samples", help="Path to the samples directory."
    )
    args = parser.parse_args()

    samples_dir = Path(args.samples_dir)
    if not samples_dir.exists():
        print(f"ERROR: samples directory not found: {samples_dir}", file=sys.stderr)
        return 2

    # what is already uploaded?
    try:
        existing = requests.get(f"{args.api_base}/documents", timeout=10).json()
    except Exception as e:
        print(f"ERROR: cannot reach backend at {args.api_base}: {e}", file=sys.stderr)
        return 2
    existing_names = {doc["filename"] for doc in existing}

    candidates = sorted(
        p
        for p in samples_dir.iterdir()
        if p.is_file()
        and p.suffix.lower() in {".pdf", ".txt"}
        and p.name != "README.md"
    )
    if not candidates:
        print(f"No .pdf or .txt files found in {samples_dir}.")
        return 1

    uploaded = 0
    skipped = 0
    for path in candidates:
        if path.name in existing_names:
            print(f"  [skip]   {path.name} (already uploaded)")
            skipped += 1
            continue
        with path.open("rb") as f:
            files = {"file": (path.name, f, "application/octet-stream")}
            response = requests.post(
                f"{args.api_base}/documents/upload",
                files=files,
                timeout=120,
            )
        if response.status_code >= 400:
            print(f"  [error]  {path.name} -> {response.status_code}: {response.text}")
            continue
        doc = response.json()
        print(f"  [up]     {path.name} -> id {doc.get('id')}")
        uploaded += 1

    print()
    print(f"Uploaded {uploaded}, skipped {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
