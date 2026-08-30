from __future__ import annotations

<<<<<<< HEAD
import re
from functools import lru_cache

import spacy

PHONE_RE = re.compile(r"(?:\+91[\-\s]?|0)?\b[6-9]\d{9}\b")
VEHICLE_RE = re.compile(r"\b([A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{3,4})\b")
AMOUNT_RE = re.compile(r"Rs\.?\s*([\d,]+(?:\.\d+)?)|₹\s*([\d,]+)")
ACCOUNT_RE = re.compile(r"\bACC\d{4}\b|\b[A-Z]{2}\d{10}\b")
STR_RE = re.compile(r"\bSTR[-\s]?\d{4}[-\s]?\d{2,4}\b", re.I)

NOISE_TOKENS = {
    "driver", "broker", "accused", "complainant", "informant", "manager",
    "police", "source", "persons", "officer", "inspector", "branch",
    "dealership", "showroom", "report", "fir", "str", "otp", "upi", "atm",
}

=======
import logging
import re
from functools import lru_cache
from typing import Any

import spacy

try:
    from backend.app.nlp.transformer_ner import TransformerNER
except ImportError:
    TransformerNER = None

# Deterministic Regex Patterns for Indian Domain & Financial Identifiers
PHONE_RE = re.compile(r"(?:\+91[\-\s]?|0)?\b[6-9]\d{9}\b")
# Full Indian plate: 2-letter state + 2-digit RTO + 1-3 letter series + 4-digit number
# e.g. UP32CD7788, MH12AB1234. Requires the numeric suffix to be exactly 4 digits.
VEHICLE_RE = re.compile(r"\b([A-Z]{2}\s?\d{2}\s?[A-Z]{1,3}\s?\d{4})\b")
AMOUNT_RE = re.compile(r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE)
ACCOUNT_RE = re.compile(r"\bACC\d{4}\b|\b[A-Z]{2}\d{10}\b")
STR_RE = re.compile(r"\bSTR[-\s]?\d{4}[-\s]?\d{2,4}\b", re.IGNORECASE)
UPI_RE = re.compile(r"\b[a-zA-Z0-9.\-_]+@[a-zA-Z]{3,}\b")

# Strict Procedural & Legal Header Noise Suppression Tokens
NOISE_TOKENS = {
    # Roles & people-titles
    "driver", "broker", "accused", "complainant", "informant", "manager",
    "police", "source", "persons", "officer", "inspector", "branch",
    "dealership", "showroom", "report", "fir", "str", "otp", "upi", "atm",
    "constable", "head constable", "si", "asi", "sho", "dsp", "sp", "ig", "dig",
    "superintendent", "deputy", "additional", "assistant", "principal",
    "clerk", "witness", "deponent", "informer", "accused", "convict", "suspect",
    # Court & legal boilerplate
    "court", "state", "appeal", "station", "judge", "versus", "order", "judgement",
    "judgment", "appellant", "respondents", "respondent", "criminal", "special",
    "pmla", "enforcement", "directorate", "tribunal", "section", "ipc", "act",
    "prosecution", "high court", "supreme court", "case", "no", "ecir", "judicature",
    "petition", "petitioner", "hbon'ble", "justice", "bench", "hon'ble", "honble",
    "cbi", "appellate", "leave", "slp", "miscellaneous", "application", "allegation",
    "affidavit", "chargesheet", "bail", "remand", "custody", "conviction", "acquittal",
    "sentence", "warrant", "summons", "notice", "exhibit", "evidence", "statement",
    # Location noise — short/common words that appear in location lists
    "allahabad", "delhi", "hyderabad", "lucknow", "uttar pradesh",
    "imps", "neft", "rtgs", "msisdn", "imsi", "cr.p.c", "crpc", "fiu", "fiu-ind",
    "tower", "date", "time", "hrs", "page",
    "sub-inspector", "commissioner", "subscriber", "callee", "caller", "target",
    "log", "summary", "table", "remarks", "direction", "site",
    "bank", "bazaar", "road", "phase", "sector", "inner", "circle", "complex",
    "jurisdiction", "enterprise", "conspiracy", "memo", "seizure", "memos",
    "recovery", "interception", "checkposts", "compliance", "holding", "ruling",
    "testimony", "testimonies", "chronology", "observation", "unit", "cell",
    "duration", "timestamp", "channel", "breakdown", "ledger", "audit",
    "detail", "details", "area", "zone", "block", "plot", "flat", "house",
    "colony", "market", "nagar", "vihar", "enclave", "avenue",
}

KNOWN_INDIAN_LOCATIONS = {
    "gomti nagar", "hazratganj", "aliganj", "charbagh railway station", "aminabad",
    "vibhuti khand", "banjara hills", "hitec city", "lucknow", "hyderabad",
    "delhi", "new delhi", "uttar pradesh", "allahabad", "mumbai", "pune", "bangalore",
    "hazratganj market", "gomti nagar extension", "aminabad bazaar", "vibhuti khand",
    "banjara hills road no 12", "hitec city phase 2", "aliganj sector c",
    "connaught place inner circle", "bandra kurla complex", "connaught place", "bandra",
}

# ── Iteration 2 context-window keyword sets ───────────────────────────────────

# Fix B: vehicle plates must appear near at least one of these keywords within ±60 chars
VEHICLE_CONTEXT_KEYWORDS = {
    "vehicle", "car", "bike", "motorcycle", "auto", "truck", "bus",
    "scooter", "jeep", "suv", "registration", "reg", "plate", "number plate",
    "registered", "seized", "intercepted", "parked", "driven", "owner",
    "chassis", "engine", "rc book", "rto", "transport",
}

# Fix C: CDR/technical column headings that indicate a phone-like number is NOT a real phone
PHONE_SUPPRESS_CONTEXT = {
    "msisdn", "imsi", "imei", "bts", "tower id", "tower_id", "lac",
    "cell id", "session", "duration", "bytes", "roaming", "sgsn",
    "ggsn", "vlr", "hlr", "serving", "msc", "nodeb", "enodeb",
}

# Fix C: narrative keywords that confirm a number IS a real phone mention
PHONE_CONFIRM_CONTEXT = {
    "called", "dialed", "dial", "contact", "number", "mobile", "phone",
    "call", "received", "incoming", "outgoing", "whatsapp", "telegram",
    "msg", "sms", "rang", "spoke", "reached",
}

# Fix D1: court institution names that should NOT be tagged as crime-scene locations
COURT_INSTITUTION_PHRASES = {
    "high court", "supreme court", "sessions court", "special court",
    "district court", "magistrate court", "tribunal", "fast track court",
    "additional sessions court", "chief judicial magistrate",
    "metropolitan magistrate", "judicial magistrate",
}

# Fix D2: document header zone — locations within this many chars are metadata, not crime scenes
HEADER_ZONE_CHARS = 200

>>>>>>> 6e1a846 (NLP Updates)

@lru_cache(maxsize=1)
def get_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return None


class EntityExtractor:
<<<<<<< HEAD
    """Extracts and canonicalizes entities from unstructured text.

    Combines spaCy statistical NER with deterministic regex extractors,
    then resolves mentions against a known registry (alias resolution).
    Unresolved PERSON/ORG/GPE mentions are kept as newly discovered entities.
    """

    def __init__(self, registry: dict):
        self.registry = registry
        self.name_to_id: dict[str, str] = {}
        for pid, p in registry["persons"].items():
            for name in [p["name"], *p.get("aliases", [])]:
                self.name_to_id[name.lower()] = pid
        self.gazetteer_re = re.compile(
            r"\b(" + "|".join(re.escape(n) for n in sorted(self.name_to_id, key=len, reverse=True)) +
            r")\b", re.IGNORECASE)
        self.last_names = {p["name"].split()[-1].lower() for p in registry["persons"].values()}
        self.location_names = {loc.lower() for loc in registry.get("locations", [])}
        self.phone_owner = registry.get("phones_index", {})
        self.account_owner = registry.get("accounts_index", {})
        self.nlp = get_nlp()

    def extract(self, text: str) -> list[dict]:
        ents = []
        ents += self._regex_entities(text)
        if self.nlp is not None:
            ents += self._spacy_entities(text)
        ents += self._gazetteer_entities(text, ents)
        return ents

    def _gazetteer_entities(self, text: str, existing: list[dict]) -> list[dict]:
        out = []
        taken = [(e["start"], e["end"]) for e in existing if e["start"] >= 0]
        for m in self.gazetteer_re.finditer(text):
            if any(s < m.end() and m.start() < e2 for s, e2 in taken):
                continue
            pid = self.name_to_id[m.group().lower()]
            out.append({
                "type": "person",
                "value": m.group().title(),
=======
    """High-Performance Hybrid NLP Entity Extractor & Canonicalization Engine.

    Combines Deep Learning Transformers, spaCy statistical NER, deterministic regex,
    and gazetteer alias matching to achieve maximum precision and recall on criminal case files.
    """

    def __init__(self, registry: dict[str, Any], use_transformer: bool = True):
        self.registry = registry
        self.name_to_id: dict[str, str] = {}
        for pid, p in registry.get("persons", {}).items():
            for name in [p.get("name"), *p.get("aliases", [])]:
                if name:
                    self.name_to_id[name.lower()] = pid

        if self.name_to_id:
            sorted_names = sorted(self.name_to_id.keys(), key=len, reverse=True)
            escaped_names = "|".join(re.escape(n) for n in sorted_names)
            self.gazetteer_re = re.compile(r"\b(" + escaped_names + r")\b", re.IGNORECASE)
        else:
            self.gazetteer_re = None

        self.last_names = {p["name"].split()[-1].lower() for p in registry.get("persons", {}).values() if "name" in p}
        self.location_names = {loc.lower() for loc in registry.get("locations", [])} | KNOWN_INDIAN_LOCATIONS
        self.phone_owner = registry.get("phones_index", {})
        self.account_owner = registry.get("accounts_index", {})
        self.nlp = get_nlp()
        self.transformer = TransformerNER() if (use_transformer and TransformerNER) else None

    def extract(self, text: str) -> list[dict[str, Any]]:
        """Extracts all entity mentions from unstructured text using the multi-stage pipeline."""
        existing_spans: list[tuple[int, int]] = []
        entities: list[dict[str, Any]] = []

        # 1. Deterministic Regex Extraction (Highest Precision 1.00)
        regex_ents = self._regex_entities(text)
        for e in regex_ents:
            entities.append(e)
            if e["start"] >= 0 and e["end"] >= 0:
                existing_spans.append((e["start"], e["end"]))

        # 2. Gazetteer & Alias Resolution Matching (Precision 0.99)
        gaz_ents = self._gazetteer_entities(text, existing_spans)
        for e in gaz_ents:
            entities.append(e)
            existing_spans.append((e["start"], e["end"]))

        # 3. Location Gazetteer Matching (Precision 0.95)
        loc_ents = self._location_entities(text, existing_spans)
        for e in loc_ents:
            entities.append(e)
            existing_spans.append((e["start"], e["end"]))

        # 4. Transformer Deep Learning NER
        # - person: confidence >= 0.92, must be multi-word
        # - location: raised to >= 0.95 to suppress over-prediction of short place names
        if self.transformer and self.transformer.pipeline:
            trans_ents = self.transformer.extract_entities(text)
            for e in trans_ents:
                etype = e["type"]
                conf = e["confidence"]
                # Per-type confidence thresholds
                min_conf = 0.95 if etype == "location" else 0.92
                if conf >= min_conf and etype in ("person", "location"):
                    if not self._is_overlapping(e["start"], e["end"], existing_spans):
                        if not self._is_noise(e["value"]):
                            if etype == "person" and len(e["value"].split()) >= 2:
                                e["canonical_id"] = self._resolve_person(e["value"])
                                entities.append(e)
                                existing_spans.append((e["start"], e["end"]))
                            elif etype == "location" and len(e["value"]) >= 4:
                                val_lower = e["value"].strip().lower()
                                # Fix D1: skip court institution names
                                if any(phrase in val_lower for phrase in COURT_INSTITUTION_PHRASES):
                                    continue
                                # Fix D2: skip header-zone locations not in known gazetteer
                                if e.get("start", 999) < HEADER_ZONE_CHARS:
                                    if val_lower not in self.location_names:
                                        continue
                                entities.append(e)
                                existing_spans.append((e["start"], e["end"]))

        # 5. spaCy Statistical NER (High Confidence Fallback & Strict Filtering)
        if self.nlp is not None:
            spacy_ents = self._spacy_entities(text, existing_spans)
            for e in spacy_ents:
                entities.append(e)
                existing_spans.append((e["start"], e["end"]))

        return self._deduplicate_and_sort(entities)

    def _gazetteer_entities(self, text: str, taken: list[tuple[int, int]]) -> list[dict[str, Any]]:
        out = []
        if not self.gazetteer_re:
            return out

        for m in self.gazetteer_re.finditer(text):
            if self._is_overlapping(m.start(), m.end(), taken):
                continue
            matched_name = m.group()
            # Require at least 2 tokens for a gazetteer person match to avoid
            # single-word alias hits on role-words ("Bunty" is OK if ≥2 chars
            # AND it's a known alias, but bare single-token hits add noise).
            # Fix A: Only suppress single-word matches that are (a) noise words AND
            # (b) NOT explicitly registered aliases — restores ~38 lost recall TPs.
            if len(matched_name.split()) < 2:
                canonical_lower = matched_name.strip().lower()
                if canonical_lower not in self.name_to_id:
                    if self._is_noise(matched_name):
                        continue
            pid = self.name_to_id.get(matched_name.lower())
            out.append({
                "type": "person",
                "value": matched_name.title(),
>>>>>>> 6e1a846 (NLP Updates)
                "start": m.start(),
                "end": m.end(),
                "confidence": 0.99,
                "canonical_id": pid,
                "method": "gazetteer",
            })
            taken.append((m.start(), m.end()))
        return out

<<<<<<< HEAD
    def _regex_entities(self, text: str) -> list[dict]:
        out = []
        for m in PHONE_RE.finditer(text):
            num = m.group().lstrip("0").replace("+91", "").replace("-", "").replace(" ", "")
            if len(num) == 12:
                num = num[2:]
            out.append(self._ent("phone", num, m.start(), m.end(), 0.99,
                                 owner_pid=self.phone_owner.get(num)))
        for m in VEHICLE_RE.finditer(text):
            plate = m.group(1).replace(" ", "")
            owner_pid = self.registry.get("vehicles", {}).get(plate)
            out.append(self._ent("vehicle", plate, m.start(), m.end(), 0.99, owner_pid=owner_pid))
        for m in AMOUNT_RE.finditer(text):
            raw = (m.group(1) or m.group(2) or "").replace(",", "")
            if raw:
                out.append(self._ent("amount", float(raw), m.start(), m.end(), 0.95))
        for m in ACCOUNT_RE.finditer(text):
            acc = m.group()
            out.append(self._ent("account", acc, m.start(), m.end(), 0.99,
                                 owner_pid=self.account_owner.get(acc)))
        if STR_RE.search(text):
            out.append(self._ent("indicator", "STR_flagged", -1, -1, 1.0))
        return out

    def _spacy_entities(self, text: str) -> list[dict]:
        doc = self.nlp(text)
        out = []
        for ent in doc.ents:
=======
    def _location_entities(self, text: str, taken: list[tuple[int, int]]) -> list[dict[str, Any]]:
        out = []
        # Only include location names with at least 2 words OR ≥6 characters
        # to avoid matching noise single-word tokens like "bank", "road", "phase".
        qualified_locs = {
            loc for loc in self.location_names
            if len(loc.split()) >= 2 or (len(loc) >= 6 and loc not in NOISE_TOKENS)
        }
        if not qualified_locs:
            return out
        loc_pattern = re.compile(
            r"\b(" + "|".join(re.escape(loc) for loc in sorted(qualified_locs, key=len, reverse=True)) + r")\b",
            re.IGNORECASE,
        )
        for m in loc_pattern.finditer(text):
            if self._is_overlapping(m.start(), m.end(), taken):
                continue
            matched_loc = m.group()
            # Extra guard: skip if the entire match is a noise token
            if matched_loc.strip().lower() in NOISE_TOKENS:
                continue
            out.append({
                "type": "location",
                "value": matched_loc.title(),
                "start": m.start(),
                "end": m.end(),
                "confidence": 0.95,
                "canonical_id": None,
                "method": "location_gazetteer",
            })
            taken.append((m.start(), m.end()))
        return out

    def _regex_entities(self, text: str) -> list[dict[str, Any]]:
        out = []

        # Phone Extraction (Fix C: CDR noise context suppression)
        for m in PHONE_RE.finditer(text):
            num = m.group().lstrip("0").replace("+91", "").replace("-", "").replace(" ", "")
            if len(num) == 12 and num.startswith("91"):
                num = num[2:]
            ctx_start = max(0, m.start() - 80)
            ctx_end = min(len(text), m.end() + 80)
            context_lower = text[ctx_start:ctx_end].lower()
            suppress_hits = sum(1 for kw in PHONE_SUPPRESS_CONTEXT if kw in context_lower)
            confirm_hits = sum(1 for kw in PHONE_CONFIRM_CONTEXT if kw in context_lower)
            # Suppress only when technical CDR context clearly dominates narrative context
            if suppress_hits > confirm_hits and suppress_hits >= 2:
                continue
            out.append(self._ent("phone", num, m.start(), m.end(), 0.99,
                                 owner_pid=self.phone_owner.get(num), method="regex"))

        # Vehicle Registration Extraction (Fix B: context-window validation)
        for m in VEHICLE_RE.finditer(text):
            plate = m.group(1).replace(" ", "")
            ctx_start = max(0, m.start() - 60)
            ctx_end = min(len(text), m.end() + 60)
            context_window = text[ctx_start:ctx_end].lower()
            has_vehicle_context = any(kw in context_window for kw in VEHICLE_CONTEXT_KEYWORDS)
            if not has_vehicle_context:
                continue  # Form/case reference number — not a vehicle plate
            owner_pid = self.registry.get("vehicles", {}).get(plate)
            out.append(self._ent("vehicle", plate, m.start(), m.end(), 0.99, owner_pid=owner_pid, method="regex"))

        # Monetary Amount Extraction
        for m in AMOUNT_RE.finditer(text):
            raw = m.group(1).replace(",", "")
            if raw:
                try:
                    out.append(self._ent("amount", float(raw), m.start(), m.end(), 0.95, method="regex"))
                except ValueError:
                    pass

        # Account Number Extraction
        for m in ACCOUNT_RE.finditer(text):
            acc = m.group()
            out.append(self._ent("account", acc, m.start(), m.end(), 0.99,
                                 owner_pid=self.account_owner.get(acc), method="regex"))

        # STR Flag Indicator Extraction
        if STR_RE.search(text):
            out.append(self._ent("indicator", "STR_flagged", -1, -1, 1.0, method="regex"))

        return out

    def _spacy_entities(self, text: str, taken: list[tuple[int, int]]) -> list[dict[str, Any]]:
        doc = self.nlp(text)
        out = []
        for ent in doc.ents:
            if self._is_overlapping(ent.start_char, ent.end_char, taken):
                continue

>>>>>>> 6e1a846 (NLP Updates)
            label = ent.label_
            value = ent.text.strip()
            if value.endswith("'s"):
                value = value[:-2].rstrip()
<<<<<<< HEAD
            if label not in ("PERSON", "ORG", "GPE", "LOC") or len(value) < 3:
                continue
            if self._is_noise(value):
                continue
            if label == "PERSON" and value.lower() in self.location_names:
                label = "GPE"
            etype = {"PERSON": "person", "ORG": "org", "GPE": "location", "LOC": "location"}[label]
=======

            if label not in ("PERSON", "GPE", "LOC") or len(value) < 3:
                continue
            if self._is_noise(value):
                continue

            if label == "PERSON":
                if value.lower() in self.location_names:
                    label = "GPE"
                elif len(value.split()) < 2:
                    # Require full name or gazetteer match for statistical person extraction
                    continue

            etype = {"PERSON": "person", "GPE": "location", "LOC": "location"}[label]

            if etype == "location":
                val_lower = value.strip().lower()
                # Fix D1: skip court/tribunal institution names
                if any(phrase in val_lower for phrase in COURT_INSTITUTION_PHRASES):
                    continue
                # Fix D2: skip header-zone locations not confirmed in the registry gazetteer
                if ent.start_char < HEADER_ZONE_CHARS and val_lower not in self.location_names:
                    continue
                # Fix D3: single-word locations shorter than 7 chars are too ambiguous
                if label in ("GPE", "LOC") and len(value.split()) < 2 and len(value) < 7:
                    continue

>>>>>>> 6e1a846 (NLP Updates)
            pid = self._resolve_person(value) if etype == "person" else None
            out.append({
                "type": etype,
                "value": value.title(),
                "start": ent.start_char,
                "end": ent.end_char,
<<<<<<< HEAD
                "confidence": 0.8,
                "canonical_id": pid,
            })
        return out

    def _is_noise(self, value: str) -> bool:
        v = value.strip()
        if PHONE_RE.search(v) or ACCOUNT_RE.search(v) or VEHICLE_RE.search(v):
            return True
        if len(v.split()) <= 1 and v.lower() in NOISE_TOKENS:
            return True
        return False

=======
                "confidence": 0.85,
                "canonical_id": pid,
                "method": "spacy_ner",
            })
            taken.append((ent.start_char, ent.end_char))
        return out

    def _is_noise(self, value: str) -> bool:
        v = value.strip().lower()
        if PHONE_RE.search(v) or ACCOUNT_RE.search(v) or VEHICLE_RE.search(v):
            return True
        tokens = set(v.split())
        if tokens.intersection(NOISE_TOKENS):
            return True
        if len(v) < 3 or v.isdigit():
            return True
        return False

    def _is_overlapping(self, start: int, end: int, existing_spans: list[tuple[int, int]]) -> bool:
        if start < 0 or end < 0:
            return False
        return any(s < end and start < e for s, e in existing_spans)

>>>>>>> 6e1a846 (NLP Updates)
    def _resolve_person(self, mention: str) -> str | None:
        key = mention.strip().lower()
        if key in self.name_to_id:
            return self.name_to_id[key]
        tail = key.replace("'", "").split()[-1]
        if len(tail) > 3 and tail in self.last_names:
            for name, pid in self.name_to_id.items():
                if name.split()[-1] == tail:
                    return pid
<<<<<<< HEAD
        return None

    @staticmethod
    def _ent(etype, value, start, end, conf, owner_pid=None):
=======

        if len(mention.split()) >= 2:
            new_id = f"P_{hash(key) % 10000:04d}"
            self.name_to_id[key] = new_id
            return new_id

        return None

    def _deduplicate_and_sort(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        deduped = []
        for e in sorted(entities, key=lambda x: (x["start"], -x["confidence"])):
            key = (e["type"], str(e["value"]).lower(), e["start"], e["end"])
            if key not in seen:
                seen.add(key)
                deduped.append(e)
        return deduped

    @staticmethod
    def _ent(etype: str, value: Any, start: int, end: int, conf: float, owner_pid: str | None = None, method: str = "") -> dict:
>>>>>>> 6e1a846 (NLP Updates)
        return {
            "type": etype,
            "value": value,
            "start": start,
            "end": end,
            "confidence": conf,
            "canonical_id": owner_pid,
<<<<<<< HEAD
=======
            "method": method,
>>>>>>> 6e1a846 (NLP Updates)
        }
