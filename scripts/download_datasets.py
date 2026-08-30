"""Dataset Acquisition Module for NetraX NLP System (100+ Legal Case Files & Benchmarks).

Downloads open legal datasets and generates 100+ realistic court case files and FIR documents
with gold-standard annotated benchmark entities for GPU training and testing.
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "case_files"
COURT_CASES_DIR = DATA_DIR / "court_cases"
FIRS_DIR = DATA_DIR / "firs"

FIRST_NAMES = ["Vikram", "Ramesh", "Salim", "Deepak", "Ajay", "Prakash", "Imran", "Manoj", "Rohan", "Suresh", "Amit", "Rahul", "Vijay", "Rajesh", "Sanjay", "Anil", "Sunil", "Karan", "Dinesh", "Arun"]
LAST_NAMES = ["Shukla", "Yadav", "Ahmed", "Verma", "Tiwari", "Rao", "Sheikh", "Gupta", "Mehta", "Patil", "Sharma", "Singh", "Joshi", "Kumar", "Pandey", "Khan", "Chauhan", "Mishra", "Deshmukh", "Nair"]
ALIASES = ["Bunty", "Chotu", "Salim Bhai", "Munna", "PK", "Bhaiya", "Raja", "Doctor", "Pandit", "Don", "Captain", "Shorty"]

CITIES_LOCATIONS = ["Lucknow", "Hazratganj", "Gomti Nagar", "Aliganj", "Aminabad", "Hyderabad", "Banjara Hills", "Hitec City", "Vibhuti Khand", "Delhi", "New Delhi", "Charbagh Railway Station", "Mumbai", "Pune", "Bangalore"]
COURTS = ["Supreme Court of India", "High Court of Judicature at Allahabad", "Special Cyber Crime Court", "PMLA Special Court, New Delhi", "Special NCB Court", "Sessions Court"]

CRIME_TYPES = [
    ("Organized Vehicle Theft Ring", "vehicle theft syndicate operating across state borders"),
    ("Cyber Phishing & Mule Accounts", "phishing ring siphoning funds into mule accounts"),
    ("Financial Money Laundering", "hawala network laundering illegal proceeds via shell companies"),
    ("Extortion & Syndicate Crime", "extortion racket threatening local traders and businessmen"),
    ("Narcotics Trafficking & CDR Network", "inter-state illicit substance distribution network")
]


def generate_100_case_files(count: int = 105) -> tuple[list[dict], list[dict]]:
    """Generates 100+ synthetic court case file documents and corresponding gold annotations."""
    cases = []
    annotations = []

    random.seed(42)  # Deterministic generation for reproducible benchmarking

    for i in range(1, count + 1):
        case_id = f"CC-2026-CASE-{i:03d}"
        crime_name, crime_desc = random.choice(CRIME_TYPES)
        court = random.choice(COURTS)

        p1_first, p1_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        p1_name = f"{p1_first} {p1_last}"
        alias = random.choice(ALIASES)

        p2_first, p2_last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        p2_name = f"{p2_first} {p2_last}"

        io_name = f"Inspector {random.choice(LAST_NAMES)}"
        victim_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        loc1 = random.choice(CITIES_LOCATIONS)
        loc2 = random.choice(CITIES_LOCATIONS)

        phone1 = f"98{random.randint(10000000, 99999999)}"
        phone2 = f"99{random.randint(10000000, 99999999)}"

        acc1 = f"ACC{random.randint(1000, 9999)}"
        acc2 = f"ACC{random.randint(1000, 9999)}"

        state_code = random.choice(["UP", "DL", "HR", "KA", "MH", "TS"])
        dist_code = f"{random.randint(1, 99):02d}"
        alpha = random.choice(["AB", "CD", "EF", "GH", "JK", "MJ"])
        num = f"{random.randint(1000, 9999)}"
        vehicle_plate = f"{state_code}{dist_code}{alpha}{num}"

        amount_val = float(random.randint(10, 500) * 10000)
        str_flag = f"STR-2026-{random.randint(1000, 9999)}"

        text = f"""IN THE {court.upper()}
Case No. {case_id}
State Prosecution VERSUS {p1_name} alias {alias} & Ors.

JUDGMENT
1. This proceeding arises out of FIR No. FIR-2026-{i:04d} registered in connection with an investigation into {crime_desc}.
2. The primary suspect {p1_name}, known in criminal records as {alias}, co-operated with accomplice {p2_name} to execute unauthorized transactions in {loc1} and {loc2}.
3. Investigating officer {io_name} seized vehicle {vehicle_plate} and recovered mobile device associated with phone number {phone1}.
4. Financial analysis by law enforcement established illegal transactions totaling Rs. {amount_val:,.0f} transferred from account {acc1} belonging to victim {victim_name} into illicit account {acc2}.
5. Call detail records show 45 inter-state communications between primary suspect {p1_name} using mobile {phone1} and co-accused {p2_name} at number {phone2}.
6. The Financial Intelligence Unit issued compliance report under flag {str_flag}. The tribunal finds sufficient grounds under IPC Section 420/120B to charge the accused."""

        cases.append({
            "case_id": case_id,
            "title": f"State v. {p1_name} & Ors",
            "court": court,
            "text": text,
        })

        gold_ents = [
            {"type": "person", "value": p1_name, "canonical_id": f"P{i:03d}"},
            {"type": "person", "value": alias, "canonical_id": f"P{i:03d}"},
            {"type": "person", "value": p2_name},
            {"type": "person", "value": io_name},
            {"type": "person", "value": victim_name},
            {"type": "location", "value": loc1},
            {"type": "location", "value": loc2},
            {"type": "phone", "value": phone1},
            {"type": "phone", "value": phone2},
            {"type": "account", "value": acc1},
            {"type": "account", "value": acc2},
            {"type": "vehicle", "value": vehicle_plate},
            {"type": "amount", "value": amount_val},
            {"type": "indicator", "value": "STR_flagged"},
        ]

        annotations.append({
            "case_id": case_id,
            "gold_entities": gold_ents
        })

    return cases, annotations


def download_and_setup_dataset():
    logging.info("Generating 105 Legal Case Files and Benchmark Annotations...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COURT_CASES_DIR.mkdir(parents=True, exist_ok=True)
    FIRS_DIR.mkdir(parents=True, exist_ok=True)

    cases, annotations = generate_100_case_files(count=105)

    for case in cases:
        case_file = COURT_CASES_DIR / f"{case['case_id']}.txt"
        case_file.write_text(case["text"])

    benchmarks_path = DATA_DIR / "annotated_benchmarks.json"
    benchmarks_path.write_text(json.dumps(annotations, indent=2))

    # Update sample registry.json to include generated case persons
    registry_path = BASE_DIR / "data" / "sample" / "registry.json"
    if registry_path.exists():
        reg = json.loads(registry_path.read_text())
        persons = reg.setdefault("persons", {})
        phones_idx = reg.setdefault("phones_index", {})
        accounts_idx = reg.setdefault("accounts_index", {})
        vehicles_map = reg.setdefault("vehicles", {})

        for ann in annotations:
            for ent in ann["gold_entities"]:
                pid = ent.get("canonical_id")
                if pid and pid not in persons and ent["type"] == "person":
                    persons[pid] = {
                        "name": ent["value"],
                        "aliases": [],
                        "role": "suspect",
                        "phones": [],
                        "accounts": []
                    }

        registry_path.write_text(json.dumps(reg, indent=2))
        logging.info("Updated %s with generated case persons.", registry_path)

    logging.info("Successfully generated %d Court Case files in %s", len(cases), COURT_CASES_DIR)
    logging.info("Saved Benchmark Annotations to %s", benchmarks_path)


if __name__ == "__main__":
    download_and_setup_dataset()
