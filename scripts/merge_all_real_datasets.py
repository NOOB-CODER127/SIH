"""Master Real Dataset Merger for NetraX NLP System.

Merges all real datasets (Hugging Face / Open Legal archives / 500+ realistic law enforcement documents)
into a unified dataset directory `data/master_unified_dataset/`.
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

UNIFIED_DATA_DIR = BASE_DIR / "data" / "master_unified_dataset"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def merge_all_datasets():
    logging.info("Starting Master Real Dataset Consolidation & Merging...")
    UNIFIED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    unified_annotations = []
    total_docs = 0

    sources = [
        BASE_DIR / "data" / "realistic_case_files" / "realistic_annotated_benchmarks.json",
        BASE_DIR / "data" / "case_files" / "bulk_annotated_benchmarks.json",
        BASE_DIR / "data" / "huggingface_kaggle_datasets" / "hf_downloaded_benchmarks.json",
    ]

    for source_file in sources:
        if source_file.exists():
            data = json.loads(source_file.read_text())
            logging.info("Merging dataset from %s (%d records)...", source_file.name, len(data))
            for item in data:
                unified_annotations.append(item)
                total_docs += 1

    # Save consolidated master benchmark
    master_benchmark_path = UNIFIED_DATA_DIR / "master_unified_benchmarks.json"
    master_benchmark_path.write_text(json.dumps(unified_annotations, indent=2))

    logging.info("Master Merge Complete! Total Unified Real Case Documents: %d in %s", total_docs, UNIFIED_DATA_DIR)
    return total_docs


if __name__ == "__main__":
    merge_all_datasets()
