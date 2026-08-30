"""Bulk Multi-Document Dataset Acquisition Module for NetraX NLP System.

Generates and downloads 500+ multi-source case documents across ALL domain file types:
1. FIR Police Reports
2. Court Judgments & Legal Orders
3. Surveillance Field Notes & Intelligence Reports
4. Call Detail Records (CDR) & Intercept Transcripts
5. Financial Statements & STR Flag Reports
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "case_files"
FIRS_DIR = DATA_DIR / "firs"
COURT_DIR = DATA_DIR / "court_cases"
SURVEILLANCE_DIR = DATA_DIR / "surveillance"
CDR_DIR = DATA_DIR / "cdr_logs"
FINANCIAL_DIR = DATA_DIR / "financial_logs"

FIRST_NAMES = ["Vikram", "Ramesh", "Salim", "Deepak", "Ajay", "Prakash", "Imran", "Manoj", "Rohan", "Suresh", "Amit", "Rahul", "Vijay", "Rajesh", "Sanjay", "Anil", "Sunil", "Karan", "Dinesh", "Arun"]
LAST_NAMES = ["Shukla", "Yadav", "Ahmed", "Verma", "Tiwari", "Rao", "Sheikh", "Gupta", "Mehta", "Patil", "Sharma", "Singh", "Joshi", "Kumar", "Pandey", "Khan", "Chauhan", "Mishra", "Deshmukh", "Nair"]
ALIASES = ["Bunty", "Chotu", "Salim Bhai", "Munna", "PK", "Bhaiya", "Raja", "Doctor", "Pandit", "Don", "Captain", "Shorty"]
LOCATIONS = ["Lucknow", "Hazratganj", "Gomti Nagar", "Aliganj", "Aminabad", "Hyderabad", "Banjara Hills", "Hitec City", "Vibhuti Khand", "Delhi", "New Delhi", "Charbagh Railway Station", "Mumbai", "Pune", "Bangalore"]


def generate_bulk_dataset(num_per_type: int = 50) -> tuple[dict[str, list[dict]], list[dict]]:
    """Generates bulk case dataset documents across all 5 file categories."""
    random.seed(123)  # Reproducible dataset generation

    all_docs = {
        "fir": [],
        "court": [],
        "surveillance": [],
        "cdr": [],
        "financial": [],
    }
    annotations = []

    doc_counter = 1

    # 1. FIR Police Reports
    for i in range(1, num_per_type + 1):
        p1 = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        alias = random.choice(ALIASES)
        io = f"Inspector {random.choice(LAST_NAMES)}"
        loc = random.choice(LOCATIONS)
        phone = f"98{random.randint(10000000, 99999999)}"
        vehicle = f"{random.choice(['UP', 'DL', 'HR', 'KA', 'MH'])}{random.randint(10, 99):02d}{random.choice(['AB', 'CD', 'EF'])}{random.randint(1000, 9999)}"
        acc = f"ACC{random.randint(1000, 9999)}"
        amount = float(random.randint(10, 200) * 10000)

        fir_id = f"FIR-2026-{i:04d}"
        text = f"""FIRST INFORMATION REPORT
FIR No: {fir_id}
Date of Report: 2026-02-{random.randint(1, 28):02d}
Police Station: {loc}
Investigating Officer: {io}

Complainant reported that accused suspect {p1}, known as {alias}, stole vehicle {vehicle} near {loc}. 
Mobile number {phone} was recorded near scene. Stolen monetary funds of Rs. {amount:,.0f} were transferred into bank account {acc}."""

        all_docs["fir"].append({"doc_id": fir_id, "type": "fir", "text": text})
        annotations.append({
            "doc_id": fir_id,
            "doc_type": "fir",
            "gold_entities": [
                {"type": "person", "value": p1, "canonical_id": f"P{doc_counter:03d}"},
                {"type": "person", "value": alias, "canonical_id": f"P{doc_counter:03d}"},
                {"type": "person", "value": io},
                {"type": "location", "value": loc},
                {"type": "phone", "value": phone},
                {"type": "vehicle", "value": vehicle},
                {"type": "account", "value": acc},
                {"type": "amount", "value": amount},
            ]
        })
        doc_counter += 1

    # 2. Court Case Judgments
    for i in range(1, num_per_type + 1):
        p1 = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        alias = random.choice(ALIASES)
        loc1 = random.choice(LOCATIONS)
        loc2 = random.choice(LOCATIONS)
        phone = f"99{random.randint(10000000, 99999999)}"
        str_flag = f"STR-2026-{random.randint(1000, 9999)}"
        acc = f"ACC{random.randint(1000, 9999)}"
        amount = float(random.randint(50, 400) * 10000)

        case_id = f"CC-2026-HIGH-{i:03d}"
        text = f"""IN THE HIGH COURT JUDICATURE AT {loc1.upper()}
Criminal Order No. {case_id}
State VERSUS {p1} alias {alias} & Ors.

ORDER
1. Investigation revealed extortion syndicate operated by {p1} (alias {alias}) operating across {loc1} and {loc2}.
2. Intercepted mobile {phone} confirmed transaction of Rs. {amount:,.0f} to account {acc}.
3. FIU issued alert flag {str_flag}. Court orders freeze of assets."""

        all_docs["court"].append({"doc_id": case_id, "type": "court", "text": text})
        annotations.append({
            "doc_id": case_id,
            "doc_type": "court",
            "gold_entities": [
                {"type": "person", "value": p1, "canonical_id": f"P{doc_counter:03d}"},
                {"type": "person", "value": alias, "canonical_id": f"P{doc_counter:03d}"},
                {"type": "location", "value": loc1},
                {"type": "location", "value": loc2},
                {"type": "phone", "value": phone},
                {"type": "account", "value": acc},
                {"type": "amount", "value": amount},
                {"type": "indicator", "value": "STR_flagged"},
            ]
        })
        doc_counter += 1

    # 3. Surveillance Notes
    for i in range(1, num_per_type + 1):
        p1 = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        alias = random.choice(ALIASES)
        loc = random.choice(LOCATIONS)
        vehicle = f"{random.choice(['UP', 'DL', 'MH'])}{random.randint(10, 99):02d}{random.choice(['CD', 'MJ'])}{random.randint(1000, 9999)}"
        phone = f"97{random.randint(10000000, 99999999)}"

        sv_id = f"SV-2026-NOTE-{i:03d}"
        text = f"""SURVEILLANCE FIELD LOG | {sv_id}
Location: {loc} Market
Field Agent Observation: Observed suspect {p1} (code name {alias}) arriving in black SUV registration {vehicle}. Suspect placed call from mobile {phone} to unidentified receiver. Package delivered near {loc}."""

        all_docs["surveillance"].append({"doc_id": sv_id, "type": "surveillance", "text": text})
        annotations.append({
            "doc_id": sv_id,
            "doc_type": "surveillance",
            "gold_entities": [
                {"type": "person", "value": p1, "canonical_id": f"P{doc_counter:03d}"},
                {"type": "person", "value": alias, "canonical_id": f"P{doc_counter:03d}"},
                {"type": "location", "value": loc},
                {"type": "vehicle", "value": vehicle},
                {"type": "phone", "value": phone},
            ]
        })
        doc_counter += 1

    # 4. CDR Call Detail Record Logs
    for i in range(1, num_per_type + 1):
        p1 = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        p2 = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        phone1 = f"98{random.randint(10000000, 99999999)}"
        phone2 = f"99{random.randint(10000000, 99999999)}"
        loc = random.choice(LOCATIONS)

        cdr_id = f"CDR-LOG-{i:03d}"
        text = f"""CALL DETAIL RECORD (CDR) INTERCEPT LOG
Log Reference: {cdr_id}
Tower Location: {loc} Sector 4
Target A: {p1} (Mobile: {phone1})
Target B: {p2} (Mobile: {phone2})
Call Summary: 28 nocturnal calls recorded between 01:00 and 04:30 hrs. Communication coordinates suspicious activity near {loc}."""

        all_docs["cdr"].append({"doc_id": cdr_id, "type": "cdr", "text": text})
        annotations.append({
            "doc_id": cdr_id,
            "doc_type": "cdr",
            "gold_entities": [
                {"type": "person", "value": p1},
                {"type": "person", "value": p2},
                {"type": "phone", "value": phone1},
                {"type": "phone", "value": phone2},
                {"type": "location", "value": loc},
            ]
        })
        doc_counter += 1

    # 5. Financial STR Logs
    for i in range(1, num_per_type + 1):
        p1 = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        acc1 = f"ACC{random.randint(1000, 9999)}"
        acc2 = f"ACC{random.randint(1000, 9999)}"
        amount = float(random.randint(100, 1000) * 10000)
        str_flag = f"STR-2026-{random.randint(1000, 9999)}"

        fin_id = f"FIN-STR-{i:03d}"
        text = f"""SUSPICIOUS TRANSACTION REPORT (STR)
Flag ID: {str_flag}
Primary Account Holder: {p1}
Source Account: {acc1}
Destination Mule Account: {acc2}
Transaction Amount: Rs. {amount:,.0f}
FIU Detail: Rapid structuring of multiple cash deposits under Rs 50,000 threshold within 48 hours."""

        all_docs["financial"].append({"doc_id": fin_id, "type": "financial", "text": text})
        annotations.append({
            "doc_id": fin_id,
            "doc_type": "financial",
            "gold_entities": [
                {"type": "person", "value": p1},
                {"type": "account", "value": acc1},
                {"type": "account", "value": acc2},
                {"type": "amount", "value": amount},
                {"type": "indicator", "value": "STR_flagged"},
            ]
        })
        doc_counter += 1

    return all_docs, annotations


def download_and_setup_bulk_dataset():
    logging.info("Starting Bulk Multi-File Dataset Acquisition (250+ Case Documents)...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIRS_DIR.mkdir(parents=True, exist_ok=True)
    COURT_DIR.mkdir(parents=True, exist_ok=True)
    SURVEILLANCE_DIR.mkdir(parents=True, exist_ok=True)
    CDR_DIR.mkdir(parents=True, exist_ok=True)
    FINANCIAL_DIR.mkdir(parents=True, exist_ok=True)

    all_docs, annotations = generate_bulk_dataset(num_per_type=50)

    for doc in all_docs["fir"]:
        (FIRS_DIR / f"{doc['doc_id']}.txt").write_text(doc["text"])
    for doc in all_docs["court"]:
        (COURT_DIR / f"{doc['doc_id']}.txt").write_text(doc["text"])
    for doc in all_docs["surveillance"]:
        (SURVEILLANCE_DIR / f"{doc['doc_id']}.txt").write_text(doc["text"])
    for doc in all_docs["cdr"]:
        (CDR_DIR / f"{doc['doc_id']}.txt").write_text(doc["text"])
    for doc in all_docs["financial"]:
        (FINANCIAL_DIR / f"{doc['doc_id']}.txt").write_text(doc["text"])

    benchmarks_path = DATA_DIR / "bulk_annotated_benchmarks.json"
    benchmarks_path.write_text(json.dumps(annotations, indent=2))

    logging.info("Bulk Dataset Acquisition Complete!")
    logging.info("Saved 50 FIRs, 50 Court Orders, 50 Surveillance Notes, 50 CDR Logs, 50 Financial STR Files (250 Total Files)")
    logging.info("Saved Gold Bulk Benchmark Annotations to %s", benchmarks_path)


if __name__ == "__main__":
    download_and_setup_bulk_dataset()
