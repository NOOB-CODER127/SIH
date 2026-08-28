from __future__ import annotations

import json
import re
from pathlib import Path


def parse_fir(path: Path) -> dict:
    text = path.read_text()
    fields = {}
    for key, pattern in {
        "fir_id": r"FIR No:\s*(\S+)",
        "date": r"Date of Report:\s*(\S+)",
        "ps": r"Police Station:\s*(.+)",
        "io": r"Investigating Officer:\s*(.+)",
    }.items():
        m = re.search(pattern, text)
        fields[key] = m.group(1).strip() if m else None
    fields["source"] = str(path)
    fields["source_type"] = "fir"
    fields["text"] = text.split("\n\n", 1)[-1].strip()
    return fields


def parse_surveillance(path: Path) -> list[dict]:
    notes = []
    for block in re.split(r"\n(?=NOTE SV-)", path.read_text().strip()):
        header, _, body = block.partition("\n")
        parts = [p.strip() for p in header.split("|")]
        if len(parts) >= 3:
            notes.append({
                "note_id": parts[0],
                "date": parts[1],
                "summary": parts[2],
                "text": body.strip(),
                "source": str(path),
                "source_type": "surveillance",
            })
    return notes


def load_cdr(path: Path) -> list[dict]:
    import csv
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_transactions(path: Path) -> list[dict]:
    import csv
    rows = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row["amount_inr"] = float(row["amount_inr"])
            rows.append(row)
    return rows


def load_registry(path: Path) -> dict:
    return json.loads(Path(path).read_text())
