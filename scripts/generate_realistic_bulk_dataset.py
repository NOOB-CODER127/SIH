"""Realistic Legal & Law Enforcement Bulk Dataset Generator for NetraX NLP.

Generates 500+ full-length, highly realistic case documents:
1. Multi-paragraph Police FIR Narratives (IPC, IT Act, PMLA sections, IO notes, witness statements)
2. High Court & Special Tribunal Judgments (Bail orders, Prosecution evidence, CDR/FIU analysis)
3. Undercover Intelligence & Surveillance Field Logs (Tailing notes, timestamps, vehicle tracking)
4. Call Detail Record (CDR) Transcripts (Tower dumps, caller/callee IDs, timestamps, durations)
5. Financial Ledgers & FIU Suspicious Transaction Reports (STRs, IMPS/UPI transfers, mule accounts)
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = Path(__file__).resolve().parent.parent
REALISTIC_DATA_DIR = BASE_DIR / "data" / "realistic_case_files"

POLICE_STATIONS = [
    ("Hazratganj PS", "Lucknow", "Uttar Pradesh Police"),
    ("Gomti Nagar PS", "Lucknow", "Uttar Pradesh Police"),
    ("Banjara Hills PS", "Hyderabad", "Telangana Police"),
    ("Hitec City Cyber PS", "Hyderabad", "Telangana Police"),
    ("Connaught Place PS", "New Delhi", "Delhi Police"),
    ("Aliganj PS", "Lucknow", "Uttar Pradesh Police"),
    ("Bandra PS", "Mumbai", "Maharashtra Police"),
]

SUSPECT_NAMES = [
    ("Vikram Shukla", "Bunty", "P001", "Vehicle Syndicate Kingpin"),
    ("Ramesh Yadav", "Chotu", "P002", "Lieutenant / Extortionist"),
    ("Salim Ahmed", "Salim Bhai", "P003", "Stolen Goods Fence"),
    ("Deepak Verma", "Doctor", "P004", "Logistics Driver"),
    ("Ajay Tiwari", "Pandit", "P005", "Syndicate Henchman"),
    ("Prakash Rao", "PK", "P010", "Cyber Crime Mastermind"),
    ("Imran Sheikh", "Raja", "P011", "Phishing Operator"),
    ("Neha Kulkarni", "Madam", "P012", "Mule Account Handler"),
    ("Suresh Patil", "Subhedar", "P013", "Hawala Broker"),
    ("Manoj Gupta", "Munna", "P020", "Financial Launderer"),
]

VICTIM_NAMES = [
    ("Rohan Mehta", "ACC9001", "P030"),
    ("Priya Singh", "ACC9002", "P031"),
    ("Kunal Joshi", "ACC9003", "P032"),
    ("Ananya Sharma", "ACC9004", "P033"),
    ("Rajesh Malhotra", "ACC9005", "P035"),
    ("Sunil Agrawal", "ACC9006", "P036"),
]

OFFICERS = ["Inspector S.K. Pandey", "Inspector R.K. Singh", "Sub-Inspector Vikram Singh", "ACP Crime Branch A.K. Varma", "Inspector Cyber Cell Priya Rao"]

LOCATIONS = ["Hazratganj Market", "Gomti Nagar Extension", "Aminabad Bazaar", "Charbagh Railway Station", "Vibhuti Khand", "Banjara Hills Road No 12", "Hitec City Phase 2", "Aliganj Sector C", "Connaught Place Inner Circle", "Bandra Kurla Complex"]

BANK_NAMES = ["HDFC Bank", "ICICI Bank", "State Bank of India", "Axis Bank", "Punjab National Bank"]


def generate_realistic_fir(doc_id: str, idx: int) -> tuple[dict, dict]:
    ps_name, city, dept = random.choice(POLICE_STATIONS)
    suspect_name, alias, pid, role = random.choice(SUSPECT_NAMES)
    victim_name, victim_acc, victim_pid = random.choice(VICTIM_NAMES)
    io_name = random.choice(OFFICERS)
    loc = random.choice(LOCATIONS)
    bank = random.choice(BANK_NAMES)

    phone_suspect = f"98{random.randint(10000000, 99999999)}"
    phone_victim = f"97{random.randint(10000000, 99999999)}"
    mule_acc = f"ACC{random.randint(1000, 9999)}"
    stolen_amount = float(random.randint(15, 600) * 10000)

    state = random.choice(["UP", "DL", "MH", "TS", "HR"])
    dist = f"{random.randint(1, 99):02d}"
    series = random.choice(["CD", "AB", "MJ", "QB", "DK"])
    plate_num = f"{random.randint(1000, 9999)}"
    vehicle_plate = f"{state}{dist}{series}{plate_num}"

    fir_num = f"FIR-2026-{idx:04d}"

    text = f"""================================================================================
FIRST INFORMATION REPORT (Under Section 154 Cr.P.C.)
{dept.upper()} | {ps_name.upper()}, {city.upper()}
FIR No: {fir_num}                                    Date & Time of FIR: 2026-03-{random.randint(1, 28):02d} T {random.randint(10, 22):02d}:30 HRS
Acts & Sections: IPC 379, IPC 420, IPC 120-B, IT Act Section 66D, PMLA Section 3
Investigating Officer: {io_name}
================================================================================

1. DETAILS OF COMPLAINANT / INFORMANT:
   Name: {victim_name}
   Contact Number: {phone_victim}
   Account Number Affected: {victim_acc} ({bank})

2. OCCURRENCE OF OFFENCE:
   Date & Time: 2026-03-{random.randint(1, 28):02d} between 19:00 HRS and 22:30 HRS
   Place of Occurrence: Near {loc}, {city}

3. DETAILED POLICE NARRATIVE & INVESTIGATION SUMMARY:
   On 2026-03-{random.randint(1, 28):02d}, complainant {victim_name} appeared at {ps_name} and submitted a written report stating that an organized criminal group executed a coordinated extortion and theft operation. 
   According to the complainant, primary suspect {suspect_name}, who is known in police intelligence records under the moniker '{alias}', approached the victim's premises near {loc} operating vehicle registration {vehicle_plate}. 
   
   Subsequent financial analysis conducted by the Investigating Officer {io_name} revealed that illicit funds amounting to Rs. {stolen_amount:,.0f} were siphoned directly from victim account {victim_acc} into mule account {mule_acc}. 
   
   Call Detail Record (CDR) analysis established that mobile number {phone_suspect}, registered under suspect {suspect_name} (alias {alias}), was active near cell tower location {loc} during the exact timeframe of the crime. Local informants confirm that suspect {suspect_name} operates as a key member ({role}) in the criminal syndicate.

4. ACTION TAKEN:
   Case registered under IPC Sections 379/420/120B. Vehicle {vehicle_plate} flagged for immediate interception across state checkposts. Bank account {mule_acc} frozen under Section 102 Cr.P.C. Investigation handed over to {io_name}.
"""

    gold = [
        {"type": "person", "value": suspect_name, "canonical_id": pid},
        {"type": "person", "value": alias, "canonical_id": pid},
        {"type": "person", "value": victim_name, "canonical_id": victim_pid},
        {"type": "person", "value": io_name},
        {"type": "location", "value": city},
        {"type": "location", "value": loc},
        {"type": "phone", "value": phone_suspect},
        {"type": "phone", "value": phone_victim},
        {"type": "vehicle", "value": vehicle_plate},
        {"type": "account", "value": victim_acc, "canonical_id": victim_pid},
        {"type": "account", "value": mule_acc},
        {"type": "amount", "value": stolen_amount},
    ]

    return {"doc_id": fir_num, "doc_type": "fir", "text": text}, {"doc_id": fir_num, "doc_type": "fir", "gold_entities": gold}


def generate_realistic_court_judgment(doc_id: str, idx: int) -> tuple[dict, dict]:
    suspect_name, alias, pid, role = random.choice(SUSPECT_NAMES)
    victim_name, victim_acc, victim_pid = random.choice(VICTIM_NAMES)
    io_name = random.choice(OFFICERS)
    loc1 = random.choice(LOCATIONS)
    loc2 = random.choice(LOCATIONS)

    phone_suspect = f"98{random.randint(10000000, 99999999)}"
    mule_acc = f"ACC{random.randint(1000, 9999)}"
    str_number = f"STR-2026-{random.randint(1000, 9999)}"
    amount = float(random.randint(50, 800) * 10000)

    case_num = f"CC-2026-JUDGMENT-{idx:04d}"

    text = f"""IN THE HIGH COURT OF JUDICATURE AT ALLAHABAD / SPECIAL PMLA TRIBUNAL
Criminal Appeal No. {idx + 4000} of 2026
Case Reference: {case_num}

STATE OF UTTAR PRADESH THROUGH PROSECUTION ... Appellant
VERSUS
{suspect_name.upper()} ALIAS {alias.upper()} & OTHERS ... Respondents

BEFORE: HON'BLE JUSTICE R.M. SHARMA & JUSTICE A.K. TRIPATHI
Date of Decision: 2026-03-{random.randint(1, 28):02d}

JUDGMENT & ORDER

1. This appeal is directed against the order of the Special Court in connection with organized crime syndicate operations across Uttar Pradesh and Delhi. The prosecution case presented by {io_name} centers on accused {suspect_name}, alias '{alias}', who functioned as {role}.

2. FINANCIAL TRAIL & FORENSIC EVIDENCE:
The Financial Intelligence Unit (FIU-IND) generated Suspicious Transaction Report reference {str_number} regarding anomalous fund flows. Investigation established that extortion funds totaling Rs. {amount:,.0f} were illegally transferred from victim {victim_name} (Account {victim_acc}) into illicit mule account {mule_acc} controlled by the accused syndicate operating out of {loc1} and {loc2}.

3. CALL DETAIL RECORD (CDR) & CELL TOWER EVIDENCE:
Technical analysis of Call Detail Records submitted by law enforcement proves continuous voice and data interactions on mobile number {phone_suspect} held by {suspect_name} (alias {alias}) traversing cell towers in {loc1} and {loc2}.

4. CONCLUSION & RULING:
Having examined the digital forensics, bank account ledgers, and witness testimonies, the Court finds overwhelming evidence establishing conspiracy under IPC Section 120-B and money laundering under PMLA Section 3/4. Bail application of accused {suspect_name} (alias {alias}) is hereby REJECTED. Direct freeze of account {mule_acc} is confirmed.
"""

    gold = [
        {"type": "person", "value": suspect_name, "canonical_id": pid},
        {"type": "person", "value": alias, "canonical_id": pid},
        {"type": "person", "value": victim_name, "canonical_id": victim_pid},
        {"type": "person", "value": io_name},
        {"type": "location", "value": loc1},
        {"type": "location", "value": loc2},
        {"type": "phone", "value": phone_suspect},
        {"type": "account", "value": victim_acc, "canonical_id": victim_pid},
        {"type": "account", "value": mule_acc},
        {"type": "amount", "value": amount},
        {"type": "indicator", "value": "STR_flagged"},
    ]

    return {"doc_id": case_num, "doc_type": "court", "text": text}, {"doc_id": case_num, "doc_type": "court", "gold_entities": gold}


def generate_realistic_surveillance_log(doc_id: str, idx: int) -> tuple[dict, dict]:
    suspect_name, alias, pid, role = random.choice(SUSPECT_NAMES)
    loc = random.choice(LOCATIONS)
    phone = f"99{random.randint(10000000, 99999999)}"

    state = random.choice(["UP", "DL", "MH", "TS"])
    vehicle = f"{state}{random.randint(10, 99):02d}CD{random.randint(1000, 9999)}"

    sv_num = f"SV-2026-INTEL-{idx:04d}"

    text = f"""CONFIDENTIAL UNDERCOVER INTELLIGENCE REPORT
SPECIAL CRIME BRANCH // SURVEILLANCE LOG
Report Reference: {sv_num}                        Date: 2026-03-{random.randint(1, 28):02d}

SUBJECT OF INTEREST:
Primary Target: {suspect_name} (Alias: '{alias}' | Role: {role})
Target Mobile: {phone}
Primary Transport: Vehicle Plate {vehicle}

FIELD OPERATIONS CHRONOLOGY:
- 14:15 HRS: Field operatives established static surveillance near {loc}. 
- 14:45 HRS: Target {suspect_name} (alias {alias}) arrived at location driving vehicle {vehicle}. Target observed making encrypted call from mobile {phone}.
- 15:30 HRS: Target met with unidentified associate outside commercial premises at {loc}. Cash package exchanged. Counter-surveillance maneuvers detected.
- 16:10 HRS: Vehicle {vehicle} departed heading towards state highway. Visual contact maintained by mobile unit. Information logged for tactical team.
"""

    gold = [
        {"type": "person", "value": suspect_name, "canonical_id": pid},
        {"type": "person", "value": alias, "canonical_id": pid},
        {"type": "location", "value": loc},
        {"type": "phone", "value": phone},
        {"type": "vehicle", "value": vehicle},
    ]

    return {"doc_id": sv_num, "doc_type": "surveillance", "text": text}, {"doc_id": sv_num, "doc_type": "surveillance", "gold_entities": gold}


def generate_realistic_cdr_transcript(doc_id: str, idx: int) -> tuple[dict, dict]:
    p1, a1, pid1, _ = random.choice(SUSPECT_NAMES)
    p2, a2, pid2, _ = random.choice(SUSPECT_NAMES)
    phone1 = f"98{random.randint(10000000, 99999999)}"
    phone2 = f"99{random.randint(10000000, 99999999)}"
    loc = random.choice(LOCATIONS)

    cdr_num = f"CDR-TOWER-LOG-{idx:04d}"

    text = f"""TELECOM INTERCEPT & TOWER DUMP ANALYSIS REPORT
LAW ENFORCEMENT TECHNICAL MONITORING CELL
Log ID: {cdr_num}                                    Target Period: 2026-03-{random.randint(1, 28):02d}

SUBSCRIBER A (CALLER): {p1} (Alias: {a1}) | MSISDN: {phone1}
SUBSCRIBER B (CALLEE): {p2} (Alias: {a2}) | MSISDN: {phone2}

CELL TOWER COVERAGE LOCATION: {loc} Tower ID #4092-B

INTERCEPT SUMMARY TABLE:
--------------------------------------------------------------------------------
Timestamp           Direction   Caller          Callee          Duration (s)  Tower Site
--------------------------------------------------------------------------------
01:14:22 HRS        OUTGOING    {phone1}       {phone2}       412 sec       {loc}
02:05:10 HRS        INCOMING    {phone2}       {phone1}       185 sec       {loc}
03:30:45 HRS        OUTGOING    {phone1}       {phone2}       520 sec       {loc}
04:12:00 HRS        OUTGOING    {phone1}       {phone2}       94 sec        {loc}
--------------------------------------------------------------------------------

ANALYTICAL REMARKS:
High nocturnal call burst (4 calls, 1211 seconds total) between suspect {p1} ({phone1}) and co-accused {p2} ({phone2}) originating from {loc} tower area between 01:00 and 04:30 AM. Indicates active conspiracy communication.
"""

    gold = [
        {"type": "person", "value": p1, "canonical_id": pid1},
        {"type": "person", "value": a1, "canonical_id": pid1},
        {"type": "person", "value": p2, "canonical_id": pid2},
        {"type": "person", "value": a2, "canonical_id": pid2},
        {"type": "phone", "value": phone1},
        {"type": "phone", "value": phone2},
        {"type": "location", "value": loc},
    ]

    return {"doc_id": cdr_num, "doc_type": "cdr", "text": text}, {"doc_id": cdr_num, "doc_type": "cdr", "gold_entities": gold}


def generate_realistic_financial_str(doc_id: str, idx: int) -> tuple[dict, dict]:
    suspect_name, alias, pid, role = random.choice(SUSPECT_NAMES)
    acc1 = f"ACC{random.randint(1000, 9999)}"
    acc2 = f"ACC{random.randint(1000, 9999)}"
    str_num = f"STR-2026-{idx + 5000:04d}"
    amount = float(random.randint(100, 1500) * 10000)
    bank = random.choice(BANK_NAMES)
    loc = random.choice(LOCATIONS)

    text = f"""FINANCIAL INTELLIGENCE UNIT (FIU-IND)
SUSPICIOUS TRANSACTION REPORT & BANK LEDGER AUDIT
STR Flag Reference: {str_num}                       Reporting Date: 2026-03-{random.randint(1, 28):02d}

ACCOUNT HOLDER AUDIT:
Target Name: {suspect_name} (Alias: {alias} | Role: {role})
Primary Account Number: {acc1} ({bank}, {loc} Branch)
Mule Destination Account: {acc2}

TRANSACTION LEDGER BREAKDOWN:
--------------------------------------------------------------------------------
Txn Date       Channel   Source Acc   Dest Acc     Amount (INR)      Risk Flag
--------------------------------------------------------------------------------
2026-03-12     IMPS      {acc1}       {acc2}       Rs. {amount:,.0f}   {str_num}
2026-03-13     NEFT      {acc1}       {acc2}       Rs. {amount/2:,.0f}   {str_num}
--------------------------------------------------------------------------------

FINANCIAL RED-FLAG ANALYSIS:
Account {acc1} held by {suspect_name} exhibited sudden rapid high-value transfers totaling Rs. {amount:,.0f} into illicit mule account {acc2} within 24 hours. Pattern matches multi-stage money laundering under PMLA.
"""

    gold = [
        {"type": "person", "value": suspect_name, "canonical_id": pid},
        {"type": "person", "value": alias, "canonical_id": pid},
        {"type": "account", "value": acc1},
        {"type": "account", "value": acc2},
        {"type": "amount", "value": amount},
        {"type": "location", "value": loc},
        {"type": "indicator", "value": "STR_flagged"},
    ]

    return {"doc_id": str_num, "doc_type": "financial", "text": text}, {"doc_id": str_num, "doc_type": "financial", "gold_entities": gold}


def build_500_realistic_dataset(num_per_category: int = 100):
    logging.info("Generating 500+ Realistic, Full-Length Law Enforcement & Case Files Dataset...")

    dirs = {
        "fir": REALISTIC_DATA_DIR / "firs",
        "court": REALISTIC_DATA_DIR / "court_cases",
        "surveillance": REALISTIC_DATA_DIR / "surveillance",
        "cdr": REALISTIC_DATA_DIR / "cdr_logs",
        "financial": REALISTIC_DATA_DIR / "financial_logs",
    }

    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    all_docs = []
    all_annotations = []

    # 1. FIRs (100)
    for i in range(1, num_per_category + 1):
        doc, ann = generate_realistic_fir(f"fir_{i}", i)
        (dirs["fir"] / f"{doc['doc_id']}.txt").write_text(doc["text"])
        all_docs.append(doc)
        all_annotations.append(ann)

    # 2. Court Judgments (100)
    for i in range(1, num_per_category + 1):
        doc, ann = generate_realistic_court_judgment(f"court_{i}", i)
        (dirs["court"] / f"{doc['doc_id']}.txt").write_text(doc["text"])
        all_docs.append(doc)
        all_annotations.append(ann)

    # 3. Surveillance Logs (100)
    for i in range(1, num_per_category + 1):
        doc, ann = generate_realistic_surveillance_log(f"sv_{i}", i)
        (dirs["surveillance"] / f"{doc['doc_id']}.txt").write_text(doc["text"])
        all_docs.append(doc)
        all_annotations.append(ann)

    # 4. CDR Logs (100)
    for i in range(1, num_per_category + 1):
        doc, ann = generate_realistic_cdr_transcript(f"cdr_{i}", i)
        (dirs["cdr"] / f"{doc['doc_id']}.txt").write_text(doc["text"])
        all_docs.append(doc)
        all_annotations.append(ann)

    # 5. Financial STR Logs (100)
    for i in range(1, num_per_category + 1):
        doc, ann = generate_realistic_financial_str(f"fin_{i}", i)
        (dirs["financial"] / f"{doc['doc_id']}.txt").write_text(doc["text"])
        all_docs.append(doc)
        all_annotations.append(ann)

    benchmarks_path = REALISTIC_DATA_DIR / "realistic_annotated_benchmarks.json"
    benchmarks_path.write_text(json.dumps(all_annotations, indent=2))

    logging.info("Successfully generated %d REALISTIC, FULL-LENGTH documents in %s", len(all_docs), REALISTIC_DATA_DIR)
    logging.info("Saved 100 FIRs, 100 Court Judgments, 100 Surveillance Logs, 100 CDR Transcripts, 100 Financial STR Files")
    logging.info("Saved Realistic Gold Annotations to %s", benchmarks_path)


if __name__ == "__main__":
    build_500_realistic_dataset(num_per_category=100)
