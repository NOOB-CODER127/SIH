import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pytest
from backend.app.ingestion.loaders import load_registry
from backend.app.nlp.entity_extractor import EntityExtractor

REGISTRY_DATA = {
    "persons": {
        "P001": {
            "name": "Vikram Shukla",
            "aliases": ["Bunty"],
            "role": "kingpin",
            "phones": ["9876543210"],
            "accounts": ["ACC1001"]
        },
        "P020": {
            "name": "Manoj Gupta",
            "aliases": ["Munna"],
            "role": "launderer",
            "phones": ["9933557788"],
            "accounts": ["ACC3003"]
        }
    },
    "vehicles": {
        "UP32CD7788": "P001"
    },
    "locations": ["Hazratganj", "Aminabad"],
    "accounts_index": {
        "ACC1001": "P001",
        "ACC3003": "P020"
    },
    "phones_index": {
        "9876543210": "P001",
        "9933557788": "P020"
    }
}


@pytest.fixture
def extractor():
    return EntityExtractor(REGISTRY_DATA, use_transformer=False)


def test_regex_extraction(extractor):
    text = "Phone number +91-9876543210 paid Rs. 14,50,000 from ACC1001 for vehicle UP32CD7788."
    ents = extractor.extract(text)

    types = {e["type"] for e in ents}
    assert "phone" in types
    assert "amount" in types
    assert "account" in types
    assert "vehicle" in types

    phone_ent = next(e for e in ents if e["type"] == "phone")
    assert phone_ent["value"] == "9876543210"
    assert phone_ent["canonical_id"] == "P001"

    amount_ent = next(e for e in ents if e["type"] == "amount")
    assert amount_ent["value"] == 1450000.0


def test_gazetteer_alias_resolution(extractor):
    text = "Bunty met with Manoj Gupta near Aminabad market."
    ents = extractor.extract(text)

    person_ents = [e for e in ents if e["type"] == "person"]
    bunty_ent = next(e for e in person_ents if "Bunty" in e["value"])
    assert bunty_ent["canonical_id"] == "P001"

    gupta_ent = next(e for e in person_ents if "Gupta" in e["value"])
    assert gupta_ent["canonical_id"] == "P020"


def test_noise_filtering(extractor):
    text = "Complainant inspector reported accused driver near police station."
    ents = extractor.extract(text)
    values = [e["value"].lower() for e in ents]

    assert "driver" not in values
    assert "complainant" not in values
    assert "inspector" not in values
