"""GPU Training and Evaluation Script for NetraX NLP System.

Designed to leverage NVIDIA GPU acceleration (CUDA) for fine-tuning spaCy / PyTorch NER models
on 100+ criminal case file datasets and evaluating performance on a held-out test split.
"""
from __future__ import annotations

import json
import logging
import random
import time
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import torch
import spacy

from backend.app.ingestion.loaders import load_registry
from backend.app.nlp.entity_extractor import EntityExtractor
from backend.app.nlp.trainer import NLPTrainer
from scripts.evaluate_nlp import evaluate_extractor

BENCHMARK_PATH = BASE_DIR / "data" / "case_files" / "annotated_benchmarks.json"
REGISTRY_PATH = BASE_DIR / "data" / "sample" / "registry.json"
MODEL_OUTPUT_DIR = BASE_DIR / "artifacts" / "nlp_gpu_model"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def check_gpu_environment():
    """Detects and reports available PyTorch / CUDA GPU hardware."""
    cuda_available = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if cuda_available else 0
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU (Fallback)"

    logging.info("================ GPU HARDWARE STATUS ================")
    logging.info("CUDA Available  : %s", cuda_available)
    logging.info("Device Count    : %d", device_count)
    logging.info("Target Device   : %s", device_name)
    if cuda_available:
        try:
            spacy.require_gpu()
            logging.info("spaCy GPU Acceleration: ENABLED (cupy/CUDA active)")
        except Exception as e:
            logging.info("spaCy GPU Acceleration note: %s (Running PyTorch CUDA pipeline)", e)
    logging.info("=====================================================")
    return cuda_available, device_name


def run_gpu_training_and_testing():
    t0 = time.time()
    cuda_available, device_name = check_gpu_environment()

    if not BENCHMARK_PATH.exists():
        logging.error("Benchmark dataset not found! Please run scripts/download_datasets.py first.")
        return

    # Load 100+ Case File Annotations
    all_benchmarks = json.loads(BENCHMARK_PATH.read_text())
    logging.info("Loaded Total Case Files Dataset: %d records", len(all_benchmarks))

    # Shuffle & Split into 80% Train, 20% Held-Out Test
    random.seed(42)
    shuffled = list(all_benchmarks)
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * 0.8)
    train_set = shuffled[:split_idx]
    test_set = shuffled[split_idx:]

    logging.info("Dataset Split: %d Training Case Files | %d Held-Out Testing Case Files", len(train_set), len(test_set))

    # Save training subset temporarily for trainer
    train_benchmark_path = BASE_DIR / "data" / "case_files" / "train_benchmarks.json"
    train_benchmark_path.write_text(json.dumps(train_set, indent=2))

    # Phase 1: Model Training / Fine-tuning
    logging.info("\n--- Phase 1: Training NLP Model on %d Case Files ---", len(train_set))
    trainer = NLPTrainer(dataset_path=train_benchmark_path, output_dir=MODEL_OUTPUT_DIR)
    trained_model_path = trainer.train_spacy_ner(iterations=15)

    # Phase 2: Evaluation on Held-Out Test Split
    logging.info("\n--- Phase 2: Testing & Benchmarking on %d Held-Out Case Files ---", len(test_set))
    registry = load_registry(REGISTRY_PATH)
    extractor = EntityExtractor(registry, use_transformer=True)

    results = evaluate_extractor(extractor, test_set)
    total_time = round(time.time() - t0, 2)

    results["gpu_info"] = {
        "cuda_available": cuda_available,
        "device_name": device_name,
        "train_case_files": len(train_set),
        "test_case_files": len(test_set),
        "total_case_files": len(all_benchmarks),
        "execution_time_seconds": total_time,
    }

    logging.info("\n================ GPU EVALUATION SUMMARY ================")
    logging.info("Device Used      : %s", device_name)
    logging.info("Overall Precision: %.2f%%", results["overall"]["precision"] * 100)
    logging.info("Overall Recall   : %.2f%%", results["overall"]["recall"] * 100)
    logging.info("Overall F1 Score : %.2f%%", results["overall"]["f1_score"] * 100)
    logging.info("Canonical Acc    : %.2f%%", results["overall"]["canonical_resolution_accuracy"] * 100)
    logging.info("Total Time       : %.2f seconds", total_time)
    logging.info("========================================================")
    logging.info("\nDetailed Entity Breakdown:\n%s", json.dumps(results["by_entity_type"], indent=2))

    # Save report
    report_path = BASE_DIR / "artifacts" / "gpu_test_results.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2))
    logging.info("Saved GPU Test Results to %s", report_path)


if __name__ == "__main__":
    run_gpu_training_and_testing()
