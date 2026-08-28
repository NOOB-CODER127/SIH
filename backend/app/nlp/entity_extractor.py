from __future__ import annotations

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


@lru_cache(maxsize=1)
def get_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return None


class EntityExtractor:
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
                "start": m.start(),
                "end": m.end(),
                "confidence": 0.99,
                "canonical_id": pid,
                "method": "gazetteer",
            })
            taken.append((m.start(), m.end()))
        return out

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
            label = ent.label_
            value = ent.text.strip()
            if value.endswith("'s"):
                value = value[:-2].rstrip()
            if label not in ("PERSON", "ORG", "GPE", "LOC") or len(value) < 3:
                continue
            if self._is_noise(value):
                continue
            if label == "PERSON" and value.lower() in self.location_names:
                label = "GPE"
            etype = {"PERSON": "person", "ORG": "org", "GPE": "location", "LOC": "location"}[label]
            pid = self._resolve_person(value) if etype == "person" else None
            out.append({
                "type": etype,
                "value": value.title(),
                "start": ent.start_char,
                "end": ent.end_char,
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

    def _resolve_person(self, mention: str) -> str | None:
        key = mention.strip().lower()
        if key in self.name_to_id:
            return self.name_to_id[key]
        tail = key.replace("'", "").split()[-1]
        if len(tail) > 3 and tail in self.last_names:
            for name, pid in self.name_to_id.items():
                if name.split()[-1] == tail:
                    return pid
        return None

    @staticmethod
    def _ent(etype, value, start, end, conf, owner_pid=None):
        return {
            "type": etype,
            "value": value,
            "start": start,
            "end": end,
            "confidence": conf,
            "canonical_id": owner_pid,
        }
