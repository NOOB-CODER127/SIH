"""NLP Model Fine-Tuning and Training Module for Criminal & Legal NER.

Fine-tunes spaCy or Hugging Face token classification models on annotated case file datasets.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from spacy.util import filter_spans

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DATASET = BASE_DIR / "data" / "case_files" / "annotated_benchmarks.json"
MODEL_OUTPUT_DIR = BASE_DIR / "artifacts" / "nlp_model"


class NLPTrainer:
    """Trainer for fine-tuning spaCy/Transformer NER pipelines on legal case files."""

    def __init__(self, dataset_path: Path = DEFAULT_DATASET, output_dir: Path = MODEL_OUTPUT_DIR):
        self.dataset_path = dataset_path
        self.output_dir = output_dir

    def train_spacy_ner(self, iterations: int = 15) -> str:
        """Fine-tunes spaCy en_core_web_sm model on case file benchmark dataset."""
        logging.info("Loading training data from %s", self.dataset_path)
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.dataset_path}")

        benchmarks = json.loads(self.dataset_path.read_text())
        nlp = spacy.load("en_core_web_sm")
        ner = nlp.get_pipe("ner")

        # Ensure all entity types are registered in the NER pipe
        for case in benchmarks:
            for ent in case.get("gold_entities", []):
                label = ent["type"].upper()
                if label in ("PERSON", "LOCATION", "VEHICLE", "ACCOUNT", "PHONE", "AMOUNT"):
                    ner.add_label(label)

        # Prepare training examples avoiding overlap
        training_data = []
        for case in benchmarks:
            doc_id = case.get("doc_id") or case.get("case_id")
            if not doc_id:
                continue

            case_text_file = None
            for subdir in ["firs", "court_cases", "surveillance", "cdr_logs", "financial_logs"]:
                cand = BASE_DIR / "data" / "case_files" / subdir / f"{doc_id}.txt"
                if cand.exists():
                    case_text_file = cand
                    break

            if not case_text_file or not case_text_file.exists():
                continue

            text = case_text_file.read_text()
            doc = nlp.make_doc(text)
            spans = []

            for ent in case["gold_entities"]:
                val = str(ent["value"])
                start = text.find(val)
                if start != -1:
                    end = start + len(val)
                    label = ent["type"].upper()
                    if label in ("PERSON", "LOCATION", "VEHICLE", "ACCOUNT", "PHONE", "AMOUNT"):
                        span = doc.char_span(start, end, label=label)
                        if span is not None:
                            spans.append(span)

            # Filter overlapping spans
            filtered_spans = filter_spans(spans)
            entities = [(s.start_char, s.end_char, s.label_) for s in filtered_spans]

            if entities:
                training_data.append((text, {"entities": entities}))

        if not training_data:
            logging.warning("No training examples compiled. Exiting trainer.")
            return str(self.output_dir)

        # Disable other pipeline components during NER training
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
        with nlp.disable_pipes(*other_pipes):
            optimizer = nlp.resume_training()
            for itn in range(iterations):
                losses = {}
                for text, annotations in training_data:
                    doc = nlp.make_doc(text)
                    example = Example.from_dict(doc, annotations)
                    nlp.update([example], drop=0.2, sgd=optimizer, losses=losses)
                logging.info("Iteration %d/%d - NER Loss: %.4f", itn + 1, iterations, losses.get("ner", 0.0))

        self.output_dir.mkdir(parents=True, exist_ok=True)
        nlp.to_disk(self.output_dir)
        logging.info("Trained model saved to %s", self.output_dir)
        return str(self.output_dir)


if __name__ == "__main__":
    trainer = NLPTrainer()
    trainer.train_spacy_ner(iterations=10)
