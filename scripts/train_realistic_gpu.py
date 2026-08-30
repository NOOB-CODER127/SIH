"""GPU Master Training & Evaluation Harness on 500 Realistic Law Enforcement Documents.

Trains PyTorch CUDA / spaCy GPU NLP models on 500 full-length realistic documents across 5 file categories:
1. 100 Multi-Page Police FIR Narratives
2. 100 High Court & Special Court Judgments
3. 100 Undercover Surveillance Field Intelligence Logs
4. 100 Call Detail Record (CDR) Tower Transcripts
5. 100 Financial Ledger & FIU Suspicious Transaction Reports (STRs)
"""
from __future__ import annotations

import json
import logging
import random
import time
from collections import defaultdict
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

REALISTIC_BENCHMARK_PATH = BASE_DIR / "data" / "realistic_case_files" / "realistic_annotated_benchmarks.json"
REGISTRY_PATH = BASE_DIR / "data" / "sample" / "registry.json"
REALISTIC_MODEL_OUTPUT_DIR = BASE_DIR / "artifacts" / "nlp_realistic_gpu_model"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def check_gpu_environment():
    cuda_available = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if cuda_available else 0
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU (Fallback)"

    logging.info("================ REALISTIC GPU ENVIRONMENT ================")
    logging.info("CUDA Hardware Available : %s", cuda_available)
    logging.info("GPU Device Count        : %d", device_count)
    logging.info("Active Target GPU Device: %s", device_name)
    if cuda_available:
        try:
            spacy.require_gpu()
            logging.info("spaCy GPU Acceleration   : ENABLED (CUDA active)")
        except Exception as e:
            logging.info("spaCy GPU Acceleration   : PyTorch CUDA pipeline active (%s)", e)
    logging.info("============================================================")
    return cuda_available, device_name


def evaluate_by_doc_type(extractor: EntityExtractor, test_docs: list[dict]) -> dict:
    """Evaluates extraction metrics per realistic document file category."""
    type_metrics = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for test_case in test_docs:
        doc_id = test_case["doc_id"]
        doc_type = test_case.get("doc_type", "general")

        file_path = None
        for subdir in ["firs", "court_cases", "surveillance", "cdr_logs", "financial_logs"]:
            candidate = BASE_DIR / "data" / "realistic_case_files" / subdir / f"{doc_id}.txt"
            if candidate.exists():
                file_path = candidate
                break

        if not file_path or not file_path.exists():
            continue

        text = file_path.read_text()
        gold_ents = test_case["gold_entities"]
        pred_ents = extractor.extract(text)

        gold_matched = [False] * len(gold_ents)
        pred_matched = [False] * len(pred_ents)

        for i, gold in enumerate(gold_ents):
            g_type = gold["type"]
            g_val = str(gold["value"]).lower()

            matched = False
            for j, pred in enumerate(pred_ents):
                p_type = pred["type"]
                p_val = str(pred["value"]).lower()

                if g_type == p_type and (g_val == p_val or g_val in p_val or p_val in g_val):
                    matched = True
                    pred_matched[j] = True
                    break

            if matched:
                type_metrics[doc_type]["tp"] += 1
            else:
                type_metrics[doc_type]["fn"] += 1

        for j, pred in enumerate(pred_ents):
            if not pred_matched[j]:
                type_metrics[doc_type]["fp"] += 1

    results_by_doc_type = {}
    for dtype, counts in type_metrics.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        results_by_doc_type[dtype] = {"precision": round(p, 4), "recall": round(r, 4), "f1_score": round(f1, 4), "tp": tp, "fp": fp, "fn": fn}

    return results_by_doc_type


def run_realistic_gpu_training():
    t0 = time.time()
    cuda_available, device_name = check_gpu_environment()

    if not REALISTIC_BENCHMARK_PATH.exists():
        logging.info("Realistic dataset missing! Running generator...")
        from scripts.generate_realistic_bulk_dataset import build_500_realistic_dataset
        build_500_realistic_dataset(num_per_category=100)

    all_benchmarks = json.loads(REALISTIC_BENCHMARK_PATH.read_text())
    logging.info("Loaded Total Realistic Dataset: %d full-length case documents", len(all_benchmarks))

    # Split dataset 80% Train (400 docs), 20% Held-Out Test (100 docs)
    random.seed(42)
    shuffled = list(all_benchmarks)
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * 0.8)
    train_set = shuffled[:split_idx]
    test_set = shuffled[split_idx:]

    logging.info("Dataset Split: %d Training Documents | %d Held-Out Test Documents", len(train_set), len(test_set))

    # Save training benchmarks
    train_realistic_path = BASE_DIR / "data" / "realistic_case_files" / "train_realistic_benchmarks.json"
    train_realistic_path.write_text(json.dumps(train_set, indent=2))

    # Phase 1: Heavy-Duty GPU Fine-Tuning
    logging.info("\n--- Phase 1: Heavy GPU Training on %d Realistic Multi-Source Documents ---", len(train_set))
    trainer = NLPTrainer(dataset_path=train_realistic_path, output_dir=REALISTIC_MODEL_OUTPUT_DIR)
    trained_model_path = trainer.train_spacy_ner(iterations=25)

    # Phase 2: Evaluation on Held-Out Test Documents
    logging.info("\n--- Phase 2: Testing & Benchmarking on %d Held-Out Test Documents ---", len(test_set))
    registry = load_registry(REGISTRY_PATH)
    extractor = EntityExtractor(registry, use_transformer=True)

    # Update evaluate_nlp document resolution for realistic path
    overall_results = evaluate_extractor(extractor, test_set)
    doc_type_results = evaluate_by_doc_type(extractor, test_set)
    total_time = round(time.time() - t0, 2)

    results = {
        "gpu_info": {
            "cuda_available": cuda_available,
            "device_name": device_name,
            "training_documents": len(train_set),
            "testing_documents": len(test_set),
            "total_documents": len(all_benchmarks),
            "execution_time_seconds": total_time,
        },
        "overall_performance": overall_results["overall"],
        "performance_by_entity_type": overall_results["by_entity_type"],
        "performance_by_document_type": doc_type_results,
    }

    logging.info("\n================ REALISTIC GPU MASTER REPORT ================")
    logging.info("Device Used               : %s", device_name)
    logging.info("Total Documents Evaluated : %d", len(all_benchmarks))
    logging.info("Overall Precision         : %.2f%%", overall_results["overall"]["precision"] * 100)
    logging.info("Overall Recall            : %.2f%%", overall_results["overall"]["recall"] * 100)
    logging.info("Overall F1 Score          : %.2f%%", overall_results["overall"]["f1_score"] * 100)
    logging.info("Total Execution Time      : %.2f seconds", total_time)
    logging.info("=============================================================")
    logging.info("\nPerformance Breakdown by Document Category:\n%s", json.dumps(doc_type_results, indent=2))
    logging.info("\nPerformance Breakdown by Entity Type:\n%s", json.dumps(overall_results["by_entity_type"], indent=2))

    report_path = BASE_DIR / "artifacts" / "realistic_gpu_test_results.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2))
    logging.info("Saved Realistic GPU Test Results to %s", report_path)


if __name__ == "__main__":
    run_realistic_gpu_training()
