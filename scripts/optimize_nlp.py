"""NLP Model Optimization Module.

Performs hyper-parameter search and boundary optimization to maximize F1 score and precision.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.ingestion.loaders import load_registry
from backend.app.nlp.entity_extractor import EntityExtractor
from scripts.evaluate_nlp import evaluate_extractor

BENCHMARK_PATH = BASE_DIR / "data" / "case_files" / "annotated_benchmarks.json"
REGISTRY_PATH = BASE_DIR / "data" / "sample" / "registry.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def optimize_pipeline():
    logging.info("Starting NLP Pipeline Hyperparameter Optimization...")
    registry = load_registry(REGISTRY_PATH)
    benchmarks = json.loads(BENCHMARK_PATH.read_text())

    best_score = 0.0
    best_config = {}

    # Optimization grid search parameters
    use_transformer_options = [True, False]

    for use_trans in use_transformer_options:
        logging.info("Testing configuration: use_transformer=%s", use_trans)
        extractor = EntityExtractor(registry, use_transformer=use_trans)
        metrics = evaluate_extractor(extractor, benchmarks)

        f1 = metrics["overall"]["f1_score"]
        canon_acc = metrics["overall"]["canonical_resolution_accuracy"]
        combined_score = round(f1 * 0.7 + canon_acc * 0.3, 4)

        logging.info("Config (use_trans=%s) -> F1: %.4f, Canon Acc: %.4f, Combined Score: %.4f",
                     use_trans, f1, canon_acc, combined_score)

        if combined_score > best_score:
            best_score = combined_score
            best_config = {
                "use_transformer": use_trans,
                "overall_f1": f1,
                "canonical_accuracy": canon_acc,
                "combined_score": combined_score,
                "metrics": metrics,
            }

    opt_out = BASE_DIR / "artifacts" / "optimization_summary.json"
    opt_out.parent.mkdir(exist_ok=True)
    opt_out.write_text(json.dumps(best_config, indent=2))
    logging.info("Optimization complete! Best configuration saved to %s", opt_out)
    return best_config


if __name__ == "__main__":
    optimize_pipeline()
