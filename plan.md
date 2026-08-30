# NetraX NLP Model Enhancement Plan

Strategic technical roadmap to optimize, fine-tune, and scale the Natural Language Processing (NLP) subsystem of the NetraX Criminal Network Analysis System to state-of-the-art performance.

---

## 1. Executive Summary & Core Objectives

The goal of this plan is to elevate entity extraction, alias resolution, and relationship detection across unstructured police FIRs, court judgments, surveillance notes, CDR call logs, and financial STR reports. 

### Target Performance Benchmarks:
* **Overall Precision**: **$\ge 90\%$** (Eliminating false positives from legal/procedural boilerplate)
* **Overall Recall**: **$\ge 95\%$** (Ensuring complete capture of criminals, locations, phones, vehicles, accounts)
* **Canonical Resolution Accuracy**: **$100\%$** (Flawlessly resolving aliases like *"Bunty"* $\rightarrow$ *Vikram Shukla*)
* **GPU Processing Speed**: **$\ge 100$ documents/sec** using CUDA batching

---

## 2. Technical Architecture & Component Upgrades

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Multi-Source Ingestion Corpus                         │
│  (FIR Narratives | Court Judgments | Surveillance Logs | CDRs | STR Reports)│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Deterministic Rule & Regex Layer (Confidence: 1.00)                      │
│    - Indian Mobile Numbers (+91 / 10-digit)                                │
│    - Vehicle Registration Plates (State Codes + Regional Series)            │
│    - Bank Account & Mule IDs (ACCxxxx / 10-16 digit)                        │
│    - Monetary Amounts (Rs. / INR / ₹)                                       │
│    - Financial Indicators (STR Flags, UPI IDs)                              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Deep Learning Transformer Layer (InLegalBERT / BERT-base-NER)            │
│    - Domain Fine-Tuned PyTorch Model on Legal & Criminal Case Files         │
│    - Softmax Token Classification + Contextual Embeddings                   │
│    - High Confidence Threshold Filtering (Score ≥ 0.90)                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. Gazetteer & Alias Disambiguation Engine                                  │
│    - Length-Sorted Trie Pattern Matching                                    │
│    - Surname & Alias Fallback Lookup                                        │
│    - Dynamic Canonical ID Generation for Discovered Suspects                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. Neural Coreference Resolution & Relation Extraction                      │
│    - Link Pronouns ("he", "the accused", "the caller") to Suspect PIDs      │
│    - Extract (Subject, Predicate, Object) triples into Knowledge Graph      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Action Plan & Phases

### Phase 1: Precision Optimization & Noise Suppression (Immediate)
* **Problem**: Procedural court headers (e.g. *"Prosecution"*, *"Appellant"*, *"Section 154"*, *"Special Court"*) trigger false positive `person` and `org` tags in spaCy/Transformers.
* **Action Items**:
  1. **Strict Title & Header Filtering**: Expand `NOISE_TOKENS` with legal procedural vocabulary.
  2. **Multi-Word Capitalization Check**: Require statistical `person` predictions to be multi-word proper nouns or matched in gazetteers.
  3. **Span Boundary Overlap Rules**: Enforce deterministic regex spans as hard boundaries that override overlapping statistical predictions.

### Phase 2: Domain Fine-Tuning on InLegalBERT & Transformer Checkpoints
* **Problem**: Off-the-shelf English news models (e.g. `dslim/bert-base-NER`) lack specialized training on Indian legal terminology and FIR structures.
* **Action Items**:
  1. Fine-tune **`InLegalBERT`** / **`Legal-BERT`** specifically on Indian criminal law corpora (`opennyai/legal_ner` & local court case files).
  2. Implement PyTorch GPU data loaders with batching (`batch_size=32`) to maximize GPU VRAM utilization on NVIDIA RTX 3050.

### Phase 3: Neural Coreference Resolution
* **Problem**: Case narratives use pronominal references like *"he called the victim"* or *"the accused received funds"* without repeating full names.
* **Action Items**:
  1. Integrate a neural coreference pipeline (`fastcoref` or `spacy-experimental` coref) to resolve pronominal mentions back to canonical person IDs (`P001`, `P020`).

### Phase 4: Subject-Verb-Object (SVO) Relation Extraction
* **Problem**: Extracting entities alone doesn't explicit capture relationships between suspects.
* **Action Items**:
  1. Build a dependency-parser relation extractor to produce structured triples:
     - `(Vikram Shukla, OWNS_VEHICLE, UP32CD7788)`
     - `(Manoj Gupta, RECEIVED_FUNDS_FROM, Rohan Mehta)`
     - `(Prakash Rao, CALLED, Imran Sheikh)`

### Phase 5: Production GPU Acceleration & Benchmarking
* **Action Items**:
  1. Export fine-tuned PyTorch models to **ONNX Runtime / TensorRT** for 5-10x inference speedup.
  2. Maintain `scripts/train_unified_master_gpu.py` as an automated continuous evaluation harness.

---

## 4. Verification & Testing Metrics

| Verification Task | Target Command | Success Criteria |
|---|---|---|
| **Bulk Dataset Generation** | `.venv/bin/python scripts/generate_realistic_bulk_dataset.py` | 500+ multi-page case files generated |
| **GPU Model Fine-Tuning** | `.venv/bin/python scripts/train_unified_master_gpu.py` | Iteration loss $< 5.0$ on NVIDIA GPU |
| **Held-Out Evaluation** | `.venv/bin/python scripts/evaluate_nlp.py` | Precision $\ge 85\%$, Recall $\ge 95\%$ |
| **Single File Analysis CLI** | `.venv/bin/python scripts/test_single_case.py` | Extracted JSON entities & canonical IDs |
| **Regression Test Suite** | `.venv/bin/pytest tests/test_nlp.py` | 100% tests passing in $< 2$ seconds |
