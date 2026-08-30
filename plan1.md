# NetraX NLP — Iteration 2 Precision Plan (`plan1.md`)

Strategic fixes for the **4 unresolved issues** from Iteration 1, targeting Overall Precision ≥ 60% while recovering lost recall.

---

## Iteration 1 Outcome Recap

| Entity | Prec (Before) | Prec (After Iter 1) | FPs | Status |
|---|---|---|---|---|
| `org` | 0% | Eliminated | 0 | ✅ Fixed |
| `location` | 29.4% | 34.8% | 277 | ⚠️ Partial |
| `person` | 45.5% | 46.9% | 310 | ⚠️ Partial + recall drop |
| `vehicle` | 43.1% | 43.1% | 70 | ❌ No change |
| `phone` | 42.7% | 42.7% | 204 | ❌ Not addressed |
| `account` | 51.1% | 51.1% | 129 | ❌ Not addressed |

---

## Issue 1 — Person Recall Regression (−38 TPs lost)

### Root Cause
The Iteration 1 `_gazetteer_entities()` guard:
```python
if len(matched_name.split()) < 2 and self._is_noise(matched_name):
    continue
```
This blocks single-word gazetteer matches that are *also* in `NOISE_TOKENS`. But valid short
aliases like `"Bunty"`, `"Raju"`, `"Imran"` may share tokens with noise words, and suspects are
often referred to by surname only (`"Shukla"`, `"Mehta"`).

### Fix A: Smarter Gazetteer Guard (`entity_extractor.py` → `_gazetteer_entities()`)

**Principle**: Only suppress a single-word match if it is a noise word AND is NOT a registered
alias/name in the registry.

```python
if len(matched_name.split()) < 2:
    canonical_lower = matched_name.strip().lower()
    # Always allow explicitly registered names/aliases
    if canonical_lower not in self.name_to_id:
        if self._is_noise(matched_name):
            continue
```

**Expected result**: Restores ~38 lost TPs for known registry aliases while still blocking
generic noisy single-word predictions from unregistered tokens.

---

## Issue 2 — Vehicle FPs Unchanged (70 FPs, 43% Precision)

### Root Cause
The stricter regex (`\d{4}` suffix) had zero effect because all 70 FPs are already in the exact
`XX\d{2}[A-Z]{1-3}\d{4}` format. They are genuine plate-looking strings from:
- **Form reference numbers** in FIRs: e.g., `"UP32GJ0012"` in a seizure report header
- **Case/file numbers** with state code prefixes: e.g., `"DL01CR4521"`
- **Structured table fields** in CDR logs using plate-format identifiers

A regex alone cannot distinguish a vehicle plate from a reference number — **context is required**.

### Fix B: Context-Window Vehicle Validation (`entity_extractor.py` → `_regex_entities()`)

**Principle**: A genuine vehicle plate mention appears near vehicle-related keywords within ±60
characters. Reference numbers appear in headers, table columns, and boilerplate without them.

```python
# Add at module level:
VEHICLE_CONTEXT_KEYWORDS = {
    "vehicle", "car", "bike", "motorcycle", "auto", "truck", "bus",
    "scooter", "jeep", "suv", "registration", "reg", "plate", "number plate",
    "registered", "seized", "intercepted", "parked", "driven", "owner",
    "chassis", "engine", "rc book", "rto", "transport",
}

# In _regex_entities(), vehicle loop:
for m in VEHICLE_RE.finditer(text):
    plate = m.group(1).replace(" ", "")
    ctx_start = max(0, m.start() - 60)
    ctx_end = min(len(text), m.end() + 60)
    context_window = text[ctx_start:ctx_end].lower()
    has_vehicle_context = any(kw in context_window for kw in VEHICLE_CONTEXT_KEYWORDS)
    if not has_vehicle_context:
        continue  # Reference/case number — not a vehicle plate
    owner_pid = self.registry.get("vehicles", {}).get(plate)
    out.append(self._ent("vehicle", plate, m.start(), m.end(), 0.99,
                         owner_pid=owner_pid, method="regex"))
```

**Expected result**: ~50 of 70 vehicle FPs eliminated. Precision improves from 43% → ~70–78%.

---

## Issue 3 — Phone FPs in CDR Documents (204 FPs, 42.7% Precision)

### Root Cause
CDR intercept logs are structured tabular data with many 10-digit numeric strings that pass
`PHONE_RE` but are NOT phone numbers:
- **Tower/BTS IDs** formatted as `91XXXXXXXXXX`
- **MSISDN/IMSI identifiers** appearing in technical column headers
- **Session/reference IDs** in columns labeled `IMEI`, `Session`, `Duration`, `Bytes`

### Fix C: CDR Noise Context Suppression (`entity_extractor.py` → `_regex_entities()`)

**Principle**: True phone mentions appear in narrative text near words like `"called"`, `"dialed"`,
`"contact"`, `"mobile"`. CDR table rows show phone-like numbers in technical column contexts.
Suppress when suppression keywords outnumber confirmation keywords.

```python
# Add at module level:
PHONE_SUPPRESS_CONTEXT = {
    "msisdn", "imsi", "imei", "bts", "tower id", "tower_id", "lac",
    "cell id", "session", "duration", "bytes", "roaming", "sgsn",
    "ggsn", "vlr", "hlr", "serving", "msc", "nodeb", "enodeb",
}

PHONE_CONFIRM_CONTEXT = {
    "called", "dialed", "dial", "contact", "number", "mobile", "phone",
    "call", "received", "incoming", "outgoing", "whatsapp", "telegram",
    "msg", "sms", "rang", "spoke", "reached",
}

# In _regex_entities(), phone loop:
for m in PHONE_RE.finditer(text):
    num = m.group().lstrip("0").replace("+91", "").replace("-", "").replace(" ", "")
    if len(num) == 12 and num.startswith("91"):
        num = num[2:]
    ctx_start = max(0, m.start() - 80)
    ctx_end = min(len(text), m.end() + 80)
    context_lower = text[ctx_start:ctx_end].lower()
    suppress_hits = sum(1 for kw in PHONE_SUPPRESS_CONTEXT if kw in context_lower)
    confirm_hits = sum(1 for kw in PHONE_CONFIRM_CONTEXT if kw in context_lower)
    # Suppress only when technical context clearly dominates narrative context
    if suppress_hits > confirm_hits and suppress_hits >= 2:
        continue
    out.append(self._ent("phone", num, m.start(), m.end(), 0.99,
                         owner_pid=self.phone_owner.get(num), method="regex"))
```

**Expected result**: Phone FPs drop from 204 → ~120–140. CDR category precision: 34.3% → ~55%.

---

## Issue 4 — Location Over-Prediction (277 FPs, 34.8% Precision)

### Root Cause (Refined After Iter 1)
Two distinct sources of remaining location FPs after the `qualified_locs` filter:

1. **Transformer LOC on court boilerplate**: `dslim/bert-base-NER` (a news model) confidently
   tags `"High Court"`, `"Sessions Court"`, `"Special Court"` as locations.
2. **spaCy GPE on document header city names**: Cities in header lines
   (`"Lucknow, dated 15-03-2024"`) are tagged as locations but are not annotated as gold crime
   scene locations.

### Fix D1: Court Institution Suppression (`entity_extractor.py`)

```python
# Add at module level:
COURT_INSTITUTION_PHRASES = {
    "high court", "supreme court", "sessions court", "special court",
    "district court", "magistrate court", "tribunal", "fast track court",
    "additional sessions court", "chief judicial magistrate",
    "metropolitan magistrate", "judicial magistrate",
}

# In extract() transformer path and _spacy_entities(), for location entities:
if etype == "location":
    val_lower = value.strip().lower()
    if any(phrase in val_lower for phrase in COURT_INSTITUTION_PHRASES):
        continue  # Court names are institutions, not crime scene locations
```

### Fix D2: Header Zone Guard (`entity_extractor.py` → `extract()`)

Locations appearing in the first 200 characters (document headers) are metadata, not crime
scene mentions. Only accept them if they are confirmed in the registry gazetteer.

```python
HEADER_ZONE_CHARS = 200

# In extract(), after each location entity is added, apply:
if etype == "location" and e.get("start", 999) < HEADER_ZONE_CHARS:
    if e["value"].lower() not in self.location_names:
        continue  # Header city name, not a crime location
```

### Fix D3: spaCy Single-Word LOC Min-Length (`entity_extractor.py` → `_spacy_entities()`)

```python
# In _spacy_entities(), for GPE/LOC labels:
if label in ("GPE", "LOC"):
    if len(value.split()) < 2 and len(value) < 7:
        continue  # Too short to be a reliable, unambiguous crime location
```

**Expected result**: Location FPs drop from 277 → ~150–180. Precision: 34.8% → ~55–65%.

---

## Summary Table

| Fix | Method Modified | FPs Removed (est.) | TPs Delta |
|---|---|---|---|
| **A** — Smarter gazetteer guard | `_gazetteer_entities()` | 0 | **+38** (recall recovery) |
| **B** — Vehicle context-window | `_regex_entities()` | **~50** | −0 |
| **C** — Phone CDR suppression | `_regex_entities()` | **~80** | −~5 |
| **D1** — Court phrase filter | `extract()` + `_spacy_entities()` | **~60** | −0 |
| **D2** — Header zone guard | `extract()` | **~40** | −~5 |
| **D3** — spaCy LOC min-length | `_spacy_entities()` | **~30** | −0 |
| **Total** | | **~260 fewer FPs** | **+28 net TPs** |

---

## Projected Metrics After Iteration 2

| Entity | Iter 1 Prec | Iter 2 Projected | Target |
|---|---|---|---|
| `person` | 46.9% | ~58–65% | ≥ 90% |
| `location` | 34.8% | ~55–65% | ≥ 90% |
| `vehicle` | 43.1% | ~70–78% | ≥ 90% |
| `phone` | 42.7% | ~58–65% | ≥ 90% |
| **Overall** | **46.2%** | **~58–65%** | **≥ 90%** |

> Reaching the 90% precision ceiling requires Phase 2 (InLegalBERT model swap). These
> heuristic iterations close the gap; the architecture change closes the remainder.

---

## Phase 2 Prerequisite: InLegalBERT Model Swap

`dslim/bert-base-NER` was trained on English news corpora (CoNLL-2003) — it has no exposure to
Indian legal terminology, FIR structure, or CDR formats. Every legal boilerplate false positive
is a consequence of this domain mismatch.

### Action
Replace in `backend/app/nlp/transformer_ner.py`:
```python
# Current:
def __init__(self, model_name_or_path: str = "dslim/bert-base-NER"):

# Replace with:
def __init__(self, model_name_or_path: str = "law-ai/InLegalBERT"):
```

Fine-tune on `opennyai/legal_ner` (12,000+ Indian legal NER annotations) using the existing
`scripts/pull_real_huggingface_datasets.py` + `backend/app/nlp/trainer.py` pipeline.

**Expected precision lift**: transformer-sourced precision 47% → ~75% on legal/court documents.

---

## Verification Plan

```bash
# After applying all Iteration 2 code changes:
.venv/bin/python scripts/train_unified_master_gpu.py
```

**Success criteria**:
- Overall Precision ≥ **60%**
- Overall Recall ≥ **80%** (must not drop below Iter 1)
- `vehicle` precision ≥ **65%**
- `phone` precision ≥ **55%**
- CDR document category precision ≥ **50%**
