# NetraX NLP Subsystem Documentation

This document provides a comprehensive technical reference for the **Natural Language Processing (NLP)** module of the NetraX Criminal Network Analysis System. It covers all NLP architecture components, entity extraction methods, regex patterns, gazetteer matching, noise filtering, data schemas, and related codebase files.

---

## 1. Overview of the NLP Module

The primary objective of the NLP subsystem is to ingest unstructured, fragmented police reports (First Information Reports - FIRs) and surveillance field notes, extract criminal entities and financial identifiers, and resolve aliases into canonical identifiers for knowledge graph construction.

### Core Capabilities
* **Statistical Named Entity Recognition (NER)**: Uses spaCy (`en_core_web_sm`) to extract named entities such as people (`PERSON`), organizations (`ORG`), and geographical locations (`GPE`, `LOC`).
* **Deterministic Regex Extraction**: Extracts structured Indian domain-specific identifiers including phone numbers, vehicle license plates, currency amounts, bank account numbers, and Suspicious Transaction Report (STR) flags.
* **Gazetteer & Alias Resolution**: Maps full names, alias aliases (e.g., *"Bunty"* $\rightarrow$ *Vikram Shukla*, *"PK"* $\rightarrow$ *Prakash Rao*), and last-name fallbacks to canonical IDs (`P001`, `P010`, etc.).
* **Contextual Noise Filtering**: Suppresses police/procedural stop words (e.g., *"complainant"*, *"driver"*, *"inspector"*, *"fir"*) and handles overlapping entity boundaries.

---

## 2. Directory & Related Files Map

The table below lists all files in the project directly related to or consumed by the NLP subsystem:

| File Path | Role in NLP Subsystem | Key Functions / Contents |
|---|---|---|
| [`backend/app/nlp/entity_extractor.py`](file:///home/srujan/Downloads/SIH-main/backend/app/nlp/entity_extractor.py) | **Core Engine** | Implements `EntityExtractor`, `get_nlp()`, spaCy NER, regex matching, noise filtering, and canonical entity resolution. |
| [`backend/app/nlp/__init__.py`](file:///home/srujan/Downloads/SIH-main/backend/app/nlp/__init__.py) | **Module Initializer** | Python package definition for `backend.app.nlp`. |
| [`backend/app/ingestion/loaders.py`](file:///home/srujan/Downloads/SIH-main/backend/app/ingestion/loaders.py) | **Text Loaders** | `parse_fir()` and `parse_surveillance()` extract raw text content from `.txt` documents. |
| [`data/sample/registry.json`](file:///home/srujan/Downloads/SIH-main/data/sample/registry.json) | **Gazetteer & Index** | Reference database containing person names, aliases, vehicle owners, locations, `phones_index`, and `accounts_index`. |
| [`data/sample/firs/*.txt`](file:///home/srujan/Downloads/SIH-main/data/sample/firs) | **Input Corpus (FIRs)** | Unstructured police FIR narratives (10 sample reports). |
| [`data/sample/surveillance.txt`](file:///home/srujan/Downloads/SIH-main/data/sample/surveillance.txt) | **Input Corpus (Notes)** | Raw field surveillance logs containing crime intelligence notes (`NOTE SV-01` to `SV-06`). |
| [`scripts/run_pipeline.py`](file:///home/srujan/Downloads/SIH-main/scripts/run_pipeline.py) | **Pipeline Execution** | Loads `registry.json`, instantiates `EntityExtractor`, runs extraction over documents, and feeds output into the Knowledge Graph builder. |
| [`scripts/generate_data.py`](file:///home/srujan/Downloads/SIH-main/scripts/generate_data.py) | **Synthetic Data Generator** | Constructs synthetic FIR narratives and surveillance text with planted entity patterns. |
| [`requirements.txt`](file:///home/srujan/Downloads/SIH-main/requirements.txt) | **Dependencies** | Declares `spacy==3.7.4` and runtime requirements. |

---

## 3. NLP Extraction Pipeline Architecture

The extraction flow follows a multi-stage hybrid approach combining deterministic regex, statistical NLP, gazetteer matching, and entity resolution:

```
                      ┌──────────────────────────────────────────────┐
                      │            Unstructured Raw Text             │
                      │   (FIR Narrative / Surveillance Log Note)    │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    1. Deterministic Regex Extractor          │
                      │  - Phone Numbers (+91 / 10-digit Indian)     │
                      │  - Vehicle Registration Plates               │
                      │  - Monetary Amounts (Rs. / ₹)                │
                      │  - Bank Account Numbers (ACCxxxx)            │
                      │  - Suspicious Transaction Flags (STR)        │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    2. spaCy Statistical NER Extractor        │
                      │  - Model: en_core_web_sm                     │
                      │  - Labels: PERSON, ORG, GPE, LOC             │
                      │  - Text Normalization & Noise Filtering      │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    3. Gazetteer & Alias Matching             │
                      │  - Match known names & alias terms           │
                      │  - Boundary collision check (avoids dupes)  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    4. Canonical Entity Resolution            │
                      │  - Map phone / account / vehicle to owner ID │
                      │  - Map alias / surname to Person ID (Pxxx)   │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │         Extracted Structured Entities        │
                      │     List[Dict] with confidence & offsets     │
                      └──────────────────────────────────────────────┘
```

---

## 4. Extraction Methods & Algorithms

### 4.1 Regular Expression Patterns

The deterministic regex patterns defined in [`entity_extractor.py`](file:///home/srujan/Downloads/SIH-main/backend/app/nlp/entity_extractor.py#L8-L12) target structured identifiers:

| Entity Type | Regex Pattern | Description / Examples | Confidence |
|---|---|---|---|
| `phone` | `(?:\+91[\-\s]?\|0)?\b[6-9]\d{9}\b` | 10-digit Indian mobile numbers starting with 6-9. Strips `+91` or leading `0`. | `0.99` |
| `vehicle` | `\b([A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{3,4})\b` | Indian vehicle registration plates (e.g., `UP32CD7788`, `HR26DK9012`, `KA05MJ4821`). | `0.99` |
| `amount` | `Rs\.?\s*([\d,]+(?:\.\d+)?)\|₹\s*([\d,]+)` | Currency values specified with `Rs.`, `Rs`, or `₹` (e.g., `Rs. 14,50,000` $\rightarrow$ `1450000.0`). | `0.95` |
| `account` | `\bACC\d{4}\b\|\b[A-Z]{2}\d{10}\b` | Bank account numbers (e.g., `ACC1001`, `ACC3003`). | `0.99` |
| `indicator` | `\bSTR[-\s]?\d{4}[-\s]?\d{2,4}\b` (re.I) | Suspicious Transaction Report reference numbers (e.g., `STR-2026-0033`). | `1.00` |

### 4.2 spaCy Statistical NER & Noise Filtering

The statistical component relies on `spacy.load("en_core_web_sm")`:
* **Target Categories**: `PERSON`, `ORG`, `GPE` (Geopolitical Entity), `LOC` (Location).
* **Possessive Trimming**: Automatically strips trailing `'s` (e.g., `"Gupta's office"` $\rightarrow$ `"Gupta"`).
* **Location Reclassification**: If spaCy labels a word as `PERSON` but it exists in the gazetteer location list (e.g., *"Aminabad"*), it is automatically reclassified to `GPE`.
* **Noise Suppression**: The `_is_noise()` function filters out:
  * Entities containing phone numbers, account numbers, or vehicle plates.
  * Single-word terms matching procedural role tokens:
    ```python
    NOISE_TOKENS = {
        "driver", "broker", "accused", "complainant", "informant", "manager",
        "police", "source", "persons", "officer", "inspector", "branch",
        "dealership", "showroom", "report", "fir", "str", "otp", "upi", "atm"
    }
    ```

### 4.3 Gazetteer Matching & Alias Resolution

1. **Gazetteer Compilation**: On initialization, `EntityExtractor` compiles all primary names and aliases from `registry.json` into a single, length-sorted regex pattern (`gazetteer_re`).
2. **Overlap Avoidance**: Gazetteer matching checks character start/end spans to avoid duplicating extractions already identified by regex.
3. **Person Resolution (`_resolve_person`)**:
   * **Direct Match**: Looks up normalized mention (lowercase) in `name_to_id`.
   * **Alias Match**: Maps known aliases (e.g., `"Bunty"` $\rightarrow$ `P001`, `"Munna"` $\rightarrow$ `P020`, `"Chotu"` $\rightarrow$ `P002`, `"PK"` $\rightarrow$ `P010`, `"Salim Bhai"` $\rightarrow$ `P003`).
   * **Surname Fallback**: Extracts the last token of a name mention (if length $> 3$) and resolves it against known registered surnames (e.g., `"Gupta"` $\rightarrow$ `P020` Manoj Gupta).

---

## 5. Extracted Entity Output Schema

Every entity returned by `EntityExtractor.extract(text)` is represented as a dictionary:

```json
{
  "type": "person",
  "value": "Vikram Shukla",
  "start": 0,
  "end": 13,
  "confidence": 0.99,
  "canonical_id": "P001",
  "method": "gazetteer"
}
```

### Field Definitions

| Field Name | Type | Description |
|---|---|---|
| `type` | `str` | One of `person`, `phone`, `vehicle`, `amount`, `account`, `location`, `org`, `indicator`. |
| `value` | `str` / `float` | Extracted string value (Title-cased for names/locations, cleaned numbers for amounts). |
| `start` | `int` | Character start index in source text (`-1` if document-level indicator). |
| `end` | `int` | Character end index in source text (`-1` if document-level indicator). |
| `confidence` | `float` | Metric score (`0.80` for spaCy NER, `0.95` for amount regex, `0.99` for gazetteer/phone/account/vehicle, `1.00` for STR indicator). |
| `canonical_id` | `str` \| `null` | Resolved entity ID from `registry.json` (e.g. `P001`, `P020`) or `null` if unmapped. |
| `method` | `str` (optional) | Extraction mechanism: `"gazetteer"`, `"spacy"`, or regex attribute. |

---

## 6. How to Run & Test the NLP Module

### Step 1: Environment Setup & spaCy Model Installation

Ensure virtual environment is active and spaCy English model is downloaded:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 2: Standalone NLP Test Script

You can test entity extraction directly on custom text using Python:

```python
import json
from backend.app.ingestion.loaders import load_registry
from backend.app.nlp.entity_extractor import EntityExtractor

# Load registry
registry = load_registry("data/sample/registry.json")
extractor = EntityExtractor(registry)

# Sample narrative
sample_text = """
Complainant Rohan Mehta reported that Bunty met Manoj Gupta near Aminabad. 
Extortion amount of Rs. 4,00,000 paid from ACC9001 to ACC3003. 
Contact number 9876543210 registered under vehicle UP32CD7788.
"""

# Extract entities
entities = extractor.extract(sample_text)
print(json.dumps(entities, indent=2))
```

### Step 3: Run Full Pipeline

To process all sample FIRs (`data/sample/firs/*.txt`) and surveillance notes (`data/sample/surveillance.txt`):

```bash
python scripts/run_pipeline.py
```

---

## 7. Roadmap & Potential NLP Enhancements

1. **Domain-Specific Transformer Model**: Fine-tune an IndicBERT or Legal-BERT model specifically on Indian crime reports for higher NER recall on Indian names and places.
2. **Coreference Resolution**: Implement neural coreference resolution (e.g., resolving pronominal references like *"he"*, *"the accused"*, *"the caller"*) to link actions back to entities.
3. **Relationship Extraction (RE)**: Extend the extractor from entity-only detection to direct subject-verb-object relation extraction (e.g., `(Vikram Shukla, OWNS, vehicle)` or `(Imran Sheikh, CALLED, Prakash Rao)`).
4. **Multilingual Ingestion**: Support cross-lingual NLP for FIRs written in Hindi or Hinglish scripts using Indic-spaCy or transformer translation pipelines.
