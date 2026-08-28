"""Generate a synthetic multi-source crime dataset with planted ground-truth patterns.

Sources produced under data/sample/:
  firs/*.txt          unstructured FIR narratives
  cdr.csv             call detail records
  transactions.csv    financial transaction records
  surveillance.txt    intelligence / surveillance notes
  registry.json       entity registry used for alias resolution during extraction

All content is fictional.
"""
import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "sample"

PERSONS = {
    "P001": {"name": "Vikram Shukla", "aliases": ["Bunty"], "role": "kingpin_vehicle_ring",
             "phones": ["9876543210"], "accounts": ["ACC1001"]},
    "P002": {"name": "Ramesh Yadav", "aliases": ["Chotu"], "role": "lieutenant",
             "phones": ["9876543211"], "accounts": []},
    "P003": {"name": "Salim Ahmed", "aliases": ["Salim Bhai"], "role": "stolen_goods_fence",
             "phones": ["9812345678"], "accounts": ["ACC1002"]},
    "P004": {"name": "Deepak Verma", "aliases": [], "role": "driver_henchman",
             "phones": ["9811223344"], "accounts": []},
    "P005": {"name": "Ajay Tiwari", "aliases": [], "role": "henchman",
             "phones": ["9988776655"], "accounts": []},

    "P010": {"name": "Prakash Rao", "aliases": ["PK"], "role": "cyber_mastermind",
             "phones": ["9000011122"], "accounts": []},
    "P011": {"name": "Imran Sheikh", "aliases": [], "role": "phishing_operator",
             "phones": ["9111222333"], "accounts": []},
    "P012": {"name": "Neha Kulkarni", "aliases": [], "role": "mule_account_holder",
             "phones": ["9848012345"], "accounts": ["ACC2002"]},
    "P013": {"name": "Suresh Patil", "aliases": [], "role": "mule_account_holder",
             "phones": ["9848098765"], "accounts": ["ACC2003"]},

    "P020": {"name": "Manoj Gupta", "aliases": ["Munna"], "role": "launderer_bridge",
             "phones": ["9933557788"], "accounts": ["ACC3003"]},

    "P030": {"name": "Rohan Mehta", "aliases": [], "role": "victim", "phones": ["9700112233"], "accounts": ["ACC9001"]},
    "P031": {"name": "Priya Singh", "aliases": [], "role": "victim", "phones": ["9700445566"], "accounts": []},
    "P032": {"name": "Kunal Joshi", "aliases": [], "role": "victim", "phones": ["9700778899"], "accounts": ["ACC9002"]},
    "P033": {"name": "Ananya Sharma", "aliases": [], "role": "bank_manager", "phones": ["9415012345"], "accounts": []},
    "P034": {"name": "S.K. Pandey", "aliases": [], "role": "investigating_officer", "phones": [], "accounts": []},
}

VEHICLES = {
    "UP32AB4455": "P004",
    "UP32CD7788": "P002",
    "MH12QB1234": None,
    "KA05MJ4821": None,
}

LOCATIONS = [
    "Gomti Nagar", "Hazratganj", "Aliganj", "Charbagh Railway Station",
    "Aminabad", "Vibhuti Khand", "Banjara Hills", "Hitec City",
]

FIRS = [
    ("FIR-2026-0041", "2026-01-06", "Hazratganj",
     "Complainant Rohan Mehta reported that his Hyundai Creta bearing registration HR26DK9012 was "
     "stolen from parking near Hazratganj at approximately 21:30 hrs on 05.01.2026. CCTV review shows "
     "a white Swift Dzire registration UP32CD7788 trailing the vehicle, driven by an unidentified male. "
     "Local sources indicate involvement of persons associated with Bunty of Gomti Nagar. Estimated "
     "vehicle value Rs. 14,50,000."),
    ("FIR-2026-0057", "2026-01-14", "Gomti Nagar",
     "Information received that a consignment of stolen two-wheelers is being kept at a shed behind "
     "Vibhuti Khand. Raid conducted. Accused Deepak Verma s/o Mahesh Verma was apprehended at spot "
     "driving pickup truck UP32AB4455 loaded with 4 motorcycles. During interrogation accused disclosed "
     "that deliveries are coordinated over phone by one Chotu who reports to Bunty. Stolen property "
     "recovered worth Rs. 6,80,000."),
    ("FIR-2026-0073", "2026-01-25", "Aminabad",
     "Businessman Kunal Joshi reported extortion demands received via calls from number 9812345678. "
     "Caller identified himself as Salim Bhai and demanded Rs. 2,00,000 monthly hafta failing which his "
     "shop in Aminabad would be damaged. Complainant submitted audio recording. Previous year similar "
     "demand was made by associates of Vikram Shukla. Amount paid last year Rs. 1,75,000 through UPI."),
    ("FIR-2026-0088", "2026-02-02", "Aliganj",
     "Complainant Priya Singh stated that on 31.01.2026 at about 23:00 hrs she was followed by a car "
     "registration MH12QB1234 near Aliganj. Two occupants passed lewd comments and threatened her when "
     "objected. Registration traced to a showroom in Noida from where the vehicle was reportedly sold by "
     "one Salim Ahmed. Driver identified as Ajay Tiwari, associate of Deepak Verma."),
    ("FIR-2026-0102", "2026-02-11", "Charbagh",
     "On secret information a naka was laid near Charbagh Railway Station. Car MH12QB1234 intercepted. "
     "Occupants fled. Search yielded 11 stolen mobile phones and fake registration plates. Documents "
     "recovered point to purchase of the car through cash payment of Rs. 3,20,000 facilitated by Munna "
     "property dealer of Vibhuti Khand."),
    ("FIR-2026-0119", "2026-02-20", "Cyber Cell",
     "Complainant Rohan Mehta reported fraudulent debit of Rs. 94,000 from his account ACC9001 after "
     "sharing OTP following a phishing SMS impersonating his bank. Traces show funds moved to account "
     "ACC2002 held by Neha Kulkarni and onward transfer of Rs. 90,000 to ACC3003 within 40 minutes. "
     "Linked complaints show similar modus operandi in 6 cases totalling Rs. 7,15,000."),
    ("FIR-2026-0127", "2026-02-24", "Cyber Cell",
     "Complainant Kunal Joshi reported phishing fraud of Rs. 61,000 from account ACC9002. Funds routed "
     "to ACC2003 held by Suresh Patil and immediately withdrawn at ATM Banjara Hills Hyderabad. Number "
     "9111222333 used for sending phishing SMS was active at Hitec City tower during same window."),
    ("FIR-2026-0135", "2026-03-01", "Gomti Nagar",
     "Specific information that kingpin Bunty alias Vikram Shukla of Gomti Nagar held a meeting with "
     "property dealer Manoj Gupta regarding purchase of two plots allegedly with proceeds of extortion "
     "and stolen vehicle sales. Meeting took place at a restaurant in Vibhuti Khand at 21:00 hrs on "
     "28.02.2026. Deal value approximated Rs. 85,00,000. Payment to be routed through banking channels "
     "of ACC3003."),
    ("FIR-2026-0141", "2026-03-05", "Hazratganj",
     "During verification of documents of seized vehicle MH12QB1234 it emerged that the vehicle was "
     "originally stolen from Bengaluru and its engine chassis numbers were tampered. Broker involved in "
     "sale identified as Salim Ahmed resident of Aminabad also holding account ACC1002 which received "
     "Rs. 2,95,000 from ACC3003 during January 2026."),
    ("FIR-2026-0148", "2026-03-09", "Aliganj",
     "Complainant Ananya Sharma branch manager reported suspicious cash deposits totalling Rs. 4,45,500 "
     "in nine instalments of Rs. 49,500 each into account ACC2002 between 02.03.2026 and 04.03.2026 by "
     "three different individuals. Deposits appear structured to avoid reporting threshold. Account "
     "holder Neha Kulkarni rarely visits branch. Branch flagged STR reference STR-2026-0033."),
]

SURVEILLANCE = """NOTE SV-01 | 2026-01-18 | Source report: Vikram Shukla aka Bunty met Salim Ahmed near Aminabad
wholesale market at 22:15 hrs. Discussion overheard regarding pending payment of Rs. 4,00,000 for three
sedans delivered. Salim assured settlement after receiving money from Munna Gupta.

NOTE SV-02 | 2026-01-27 | Technical surveillance: number 9876543210 (Vikram Shukla) in repeated contact
with 9933557788 (Manoj Gupta). Also observed 9988776655 (Ajay Tiwari) shadowing Gupta's office in Vibhuti Khand.

NOTE SV-03 | 2026-02-14 | Cyber cell input: number 9111222333 (Imran Sheikh) in nightly contact with
9000011122 registered at Banjara Hills believed to be Prakash Rao alias PK. Calls typically between
0100 and 0400 hrs lasting 20-45 minutes. Content unknown.

NOTE SV-04 | 2026-02-21 | Source report: Manoj Gupta hosted lunch at his farmhouse, Gomti Nagar bypass,
attended by Vikram Shukla, Ramesh Yadav and unidentified persons arriving in car bearing registration
KA05MJ4821. Vehicle suspected to be from Bengaluru theft chain.

NOTE SV-05 | 2026-03-02 | Financial intel: multiple sub-threshold cash credits into ACC2002 detected.
Account previously dormant became hyperactive. Withdrawals replaced by instant transfers to ACC3003
(Manoj Gupta) suggesting mule-to-layering behaviour.

NOTE SV-06 | 2026-03-08 | Cross-unit meeting input: Prakash Rao travelled to Lucknow by air, met Manoj
Gupta at Hitec City partner office prior to travel. Indicates coordination between cyber cell and
Lucknow based network for fund placement through property deals."""


def gen_cdr():
    rows = []
    t0 = datetime(2026, 1, 1)
    towers = ["LKO_GN_07", "LKO_HZ_02", "LKO_AL_11", "LKO_CH_04", "LKO_AM_09", "HYD_BH_03", "HYD_HC_01"]

    def call(a, b, day, hour, minute=0, dur=120):
        ts = t0 + timedelta(days=day, hours=hour, minutes=minute)
        rows.append([ts.strftime("%Y-%m-%d %H:%M:%S"), a, b, dur, random.choice(towers)])

    def noise(day):
        pool = [p["phones"][0] for p in PERSONS.values() if p["phones"]]
        for _ in range(random.randint(3, 6)):
            a, b = random.sample(pool, 2)
            call(a, b, day, random.randint(8, 22), random.randint(0, 59), random.randint(10, 300))

    g1 = ["9876543210", "9876543211", "9812345678", "9811223344", "9988776655"]
    bridge = "9933557788"
    for d in range(70):
        for _ in range(random.randint(1, 3)):
            a, b = random.sample(g1[:3], 2)
            call(a, b, d, random.randint(9, 23), random.randint(0, 59), random.randint(60, 400))
        if random.random() < 0.7:
            call("9876543210", bridge, d, random.randint(10, 22), random.randint(0, 59), random.randint(90, 350))
        if random.random() < 0.5:
            call("9812345678", bridge, d, random.randint(10, 21), random.randint(0, 59), random.randint(60, 240))
        if d % 3 == 0 and random.random() < 0.6:
            call("9811223344", "9988776655", d, random.randint(18, 23), random.randint(0, 59), random.randint(60, 260))
        if random.random() < 0.4:
            call("9000011122", bridge, d, random.randint(11, 20), random.randint(0, 59), random.randint(60, 180))
        if d % 2 == 1:
            for _ in range(random.randint(1, 3)):
                call("9111222333", "9000011122", d, random.randint(1, 4), random.randint(0, 59),
                     random.randint(1200, 2700))
        if random.random() < 0.5:
            call("9111222333", "9848012345", d, random.randint(9, 21), random.randint(0, 59), random.randint(30, 150))
        noise(d)

    rows.sort(key=lambda r: r[0])
    with open(DATA / "cdr.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "caller_number", "callee_number", "duration_sec", "cell_tower"])
        w.writerows(rows)
    return len(rows)


def gen_transactions():
    rows = []
    t0 = datetime(2026, 1, 1)

    def tx(ts, frm, to, amount, mode, note=""):
        rows.append([ts.strftime("%Y-%m-%d %H:%M:%S"), frm, to, amount, mode, note])

    for i, day in enumerate(range(2, 5)):
        for j in range(3):
            ts = t0 + timedelta(days=day, hours=random.randint(10, 16), minutes=random.randint(0, 59))
            tx(ts, "CASH", "ACC2002", 49500, "cash_deposit", f"structuring_deposit_{i}_{j}")
    base = t0 + timedelta(days=5, hours=13, minutes=10)
    tx(base, "ACC2002", "ACC3003", 145000, "neft", "layering_hop_1")
    tx(base + timedelta(minutes=38), "ACC3003", "ACC1001", 140000, "neft", "layering_hop_2")
    tx(base + timedelta(hours=2, minutes=15), "ACC1001", "CASH", 135000, "atm_withdrawal", "layering_exit")

    hop2 = t0 + timedelta(days=12, hours=11, minutes=5)
    tx(hop2, "ACC2003", "ACC3003", 92000, "imps", "layering_hop_1")
    tx(hop2 + timedelta(minutes=51), "ACC3003", "ACC1002", 90000, "imps", "layering_hop_2")

    for amt, day in [(295000, 17), (175000, 34), (210000, 49)]:
        ts = t0 + timedelta(days=day, hours=random.randint(11, 17))
        tx(ts, "ACC3003", "ACC1002", amt, "rtgs", "fence_settlement")
        tx(ts + timedelta(days=2, hours=random.randint(1, 5)), "ACC1002", "ACC1001", int(amt * 0.6), "neft",
           "kickback_kingpin")

    tx(t0 + timedelta(days=58, hours=12), "ACC3003", "ACC1001", 850000, "rtgs", "land_deal_payment")
    tx(t0 + timedelta(days=59, hours=15), "ACC1001", "ACC3003", 400000, "neft", "partial_return")

    for i in range(40):
        day = random.randint(0, 68)
        accs = ["ACC9001", "ACC9002"]
        a = random.choice(accs)
        b = random.choice(["MERCH001", "MERCH002", "UTIL001", "ACC9002" if a == "ACC9001" else "ACC9001"])
        tx(t0 + timedelta(days=day, hours=random.randint(8, 21), minutes=random.randint(0, 59)),
           a, b, random.choice([250, 480, 750, 1200, 2500, 3800, 6500]), random.choice(["upi", "debit_card"]),
           "routine_noise")

    rows.sort(key=lambda r: r[0])
    with open(DATA / "transactions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "from_account", "to_account", "amount_inr", "mode", "note"])
        w.writerows(rows)
    return len(rows)


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    fir_dir = DATA / "firs"
    fir_dir.mkdir(exist_ok=True)
    for fir_no, date, ps, text in FIRS:
        body = (
            f"FIRST INFORMATION REPORT\n"
            f"FIR No: {fir_no}\n"
            f"Date of Report: {date}\n"
            f"Police Station: {ps}\n"
            f"Investigating Officer: Inspector S.K. Pandey\n\n"
            f"{text}\n"
        )
        (fir_dir / f"{fir_no}.txt").write_text(body)

    (DATA / "surveillance.txt").write_text(SURVEILLANCE)

    registry = {
        "persons": PERSONS,
        "vehicles": VEHICLES,
        "locations": LOCATIONS,
        "accounts_index": {acc: pid for pid, p in PERSONS.items() for acc in p["accounts"]},
        "phones_index": {ph: pid for pid, p in PERSONS.items() for ph in p["phones"]},
    }
    (DATA / "registry.json").write_text(json.dumps(registry, indent=2))

    n_cdr = gen_cdr()
    n_tx = gen_transactions()
    print(f"Generated {len(FIRS)} FIRs, {n_cdr} CDR rows, {n_tx} transactions, "
          f"{len(SURVEILLANCE.splitlines())//3} surveillance notes, registry.json")


if __name__ == "__main__":
    main()
