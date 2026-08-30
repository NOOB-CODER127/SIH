"""NLP Evaluation & Benchmarking Module.

Evaluates entity extraction performance (Precision, Recall, F1 Score, Canonical Accuracy)
against gold-standard annotated court case and FIR benchmarks.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys_path = [str(BASE_DIR)]
import sys
sys.path.extend(sys_path)

from backend.app.ingestion.loaders import load_registry
from backend.app.nlp.entity_extractor import EntityExtractor

BENCHMARK_PATH = BASE_DIR / "data" / "case_files" / "annotated_benchmarks.json"
REGISTRY_PATH = BASE_DIR / "data" / "sample" / "registry.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def evaluate_extractor(extractor: EntityExtractor, benchmarks: list[dict]) -> dict:
    """Computes Precision, Recall, F1 score, and Canonical Resolution accuracy."""
    metrics_by_type = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    canonical_correct = 0
    canonical_total = 0

    for test_case in benchmarks:
        doc_id = test_case.get("doc_id") or test_case.get("case_id")
        if not doc_id:
            continue

        text_file = None
        for base_dir_name in ["case_files", "realistic_case_files"]:
            for subdir in ["firs", "court_cases", "surveillance", "cdr_logs", "financial_logs"]:
                cand = BASE_DIR / "data" / base_dir_name / subdir / f"{doc_id}.txt"
                if cand.exists():
                    text_file = cand
                    break
            if text_file:
                break

        if not text_file or not text_file.exists():
            continue

        text = text_file.read_text()
        gold_ents = test_case["gold_entities"]
        pred_ents = extractor.extract(text)

        # Build Gold & Predicted canonical sets
        gold_matched = [False] * len(gold_ents)
        pred_matched = [False] * len(pred_ents)

        for i, gold in enumerate(gold_ents):
            g_type = gold["type"]
            g_val = str(gold["value"]).lower()
            g_canon = gold.get("canonical_id")

            matched = False
            for j, pred in enumerate(pred_ents):
                p_type = pred["type"]
                p_val = str(pred["value"]).lower()
                p_canon = pred.get("canonical_id")

                # Match logic: exact value or substring match within type
                if g_type == p_type and (g_val == p_val or g_val in p_val or p_val in g_val):
                    matched = True
                    pred_matched[j] = True

                    if g_canon is not None:
                        canonical_total += 1
                        if g_canon == p_canon:
                            canonical_correct += 1
                    break

            if matched:
                gold_matched[i] = True
                metrics_by_type[g_type]["tp"] += 1
            else:
                metrics_by_type[g_type]["fn"] += 1

        for j, pred in enumerate(pred_ents):
            if not pred_matched[j]:
                metrics_by_type[pred["type"]]["fp"] += 1

    # Aggregate overall metrics
    overall_tp = sum(m["tp"] for m in metrics_by_type.values())
    overall_fp = sum(m["fp"] for m in metrics_by_type.values())
    overall_fn = sum(m["fn"] for m in metrics_by_type.values())

    def calc_p_r_f1(tp, fp, fn):
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return round(precision, 4), round(recall, 4), round(f1, 4)

    per_type_results = {}
    for etype, counts in metrics_by_type.items():
        p, r, f1 = calc_p_r_f1(counts["tp"], counts["fp"], counts["fn"])
        per_type_results[etype] = {"precision": p, "recall": r, "f1_score": f1, "tp": counts["tp"], "fp": counts["fp"], "fn": counts["fn"]}

    overall_p, overall_r, overall_f1 = calc_p_r_f1(overall_tp, overall_fp, overall_fn)
    canon_acc = round(canonical_correct / canonical_total, 4) if canonical_total > 0 else 0.0

    return {
        "overall": {
            "precision": overall_p,
            "recall": overall_r,
            "f1_score": overall_f1,
            "canonical_resolution_accuracy": canon_acc,
            "total_true_positives": overall_tp,
            "total_false_positives": overall_fp,
            "total_false_negatives": overall_fn,
        },
        "by_entity_type": per_type_results,
    }


def main():
    logging.info("Starting NLP Evaluation on Case Files Dataset...")
    if not BENCHMARK_PATH.exists():
        logging.error("Benchmark dataset not found at %s. Please run scripts/download_datasets.py first.", BENCHMARK_PATH)
        return

    registry = load_registry(REGISTRY_PATH)
    benchmarks = json.loads(BENCHMARK_PATH.read_text())

    extractor = EntityExtractor(registry)
    results = evaluate_extractor(extractor, benchmarks)

    logging.info("===== EVALUATION BENCHMARK RESULTS =====")
    logging.info("Overall Precision : %.2f%%", results["overall"]["precision"] * 100)
    logging.info("Overall Recall    : %.2f%%", results["overall"]["recall"] * 100)
    logging.info("Overall F1 Score  : %.2f%%", results["overall"]["f1_score"] * 100)
    logging.info("Canonical Accuracy: %.2f%%", results["overall"]["canonical_resolution_accuracy"] * 100)
    logging.info("\nBreakdown by Entity Type:\n%s", json.dumps(results["by_entity_type"], indent=2))

    eval_out = BASE_DIR / "artifacts" / "evaluation_results.json"
    eval_out.parent.mkdir(exist_ok=True)
    eval_out.write_text(json.dumps(results, indent=2))
    logging.info("Full evaluation results saved to %s", eval_out)


if __name__ == "__main__":
    main()
