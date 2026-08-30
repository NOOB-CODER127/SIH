"""Transformer-based NER Engine for Legal & Criminal Text Extraction.

Provides Deep Learning NER capabilities using Hugging Face Transformers models
(e.g., dslim/bert-base-NER or InLegalBERT) with graceful fallback to spaCy NER.
"""
from __future__ import annotations

import logging
from typing import Any

logging.basicConfig(level=logging.INFO)

LABEL_MAP = {
    "PER": "person",
    "PERSON": "person",
    "B-PER": "person",
    "I-PER": "person",
    "LOC": "location",
    "LOCATION": "location",
    "GPE": "location",
    "B-LOC": "location",
    "I-LOC": "location",
    # ORG intentionally excluded: gold schema has no org entities;
    # every ORG prediction was a false positive (+117 FPs).
}


class TransformerNER:
    """Transformer-based NER model extractor."""

    def __init__(self, model_name_or_path: str = "dslim/bert-base-NER"):
        self.model_name = model_name_or_path
        self.pipeline = None
        self._init_pipeline()

    def _init_pipeline(self):
        try:
            from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

            logging.info("Initializing Transformer NER pipeline with model: %s", self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            self.pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
            logging.info("Transformer NER pipeline initialized successfully.")
        except Exception as e:
            logging.warning("Transformer model unavailable (%s). Falling back to spaCy/Hybrid extractor.", e)
            self.pipeline = None

    def extract_entities(self, text: str) -> list[dict[str, Any]]:
        """Runs Transformer NER over text and converts results to standardized schema."""
        if self.pipeline is None:
            return []

        try:
            raw_entities = self.pipeline(text)
            entities = []
            for item in raw_entities:
                entity_group = item.get("entity_group") or item.get("entity")
                norm_label = LABEL_MAP.get(entity_group, None)
                if not norm_label:
                    continue

                value = item["word"].strip()
                # Clean word tokens if split by subwords
                if value.startswith("##"):
                    value = value[2:]

                start = int(item["start"])
                end = int(item["end"])
                score = float(item["score"])

                if len(value) < 2:
                    continue

                entities.append({
                    "type": norm_label,
                    "value": value.title(),
                    "start": start,
                    "end": end,
                    "confidence": round(score, 4),
                    "method": "transformer_ner",
                })
            return entities
        except Exception as e:
            logging.error("Error during Transformer NER extraction: %s", e)
            return []
