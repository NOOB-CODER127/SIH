"""Single Case File NLP & Network Analysis CLI Test Runner.

Feeds any custom case text file into the NLP engine and displays extracted entities,
canonical ID resolutions, confidence scores, and knowledge graph linkages.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.ingestion.loaders import load_registry
from backend.app.nlp.entity_extractor import EntityExtractor


def analyze_case_text(text: str, registry_path: Path = BASE_DIR / "data" / "sample" / "registry.json") -> dict:
    registry = load_registry(registry_path)
    extractor = EntityExtractor(registry, use_transformer=True)

    entities = extractor.extract(text)

    # Group entities by type
    grouped = {}
    for e in entities:
        t = e["type"]
        grouped.setdefault(t, []).append(e)

    summary = {
        "text_length": len(text),
        "total_entities_extracted": len(entities),
        "entity_counts_by_type": {k: len(v) for k, v in grouped.items()},
        "extracted_entities": entities,
    }
    return summary


def main():
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if file_path.exists():
            text = file_path.read_text()
            print(f"--- Analyzing Case File: {file_path} ---")
        else:
            text = sys.argv[1]
            print("--- Analyzing Custom Input Text ---")
    else:
        # Sample case text for demonstration
        text = """
IN THE SPECIAL COURT FOR ECONOMIC OFFENCES, LUCKNOW
FIR No: FIR-2026-0099
Investigating Officer: Inspector S.K. Pandey

Prosecution reports that kingpin Vikram Shukla (P001), alias Bunty, coordinated with 
Manoj Gupta (P020), alias Munna, to launder extortion money. 
Extortion amount of Rs. 14,50,000 was transferred from victim Rohan Mehta account ACC9001 
into mule account ACC3003 at Aminabad. 
Suspect vehicle UP32CD7788 was tracked using mobile 9876543210 near Hazratganj. 
Financial Intelligence Unit issued indicator STR-2026-0033.
"""
        print("--- Analyzing Sample Case File ---")

    result = analyze_case_text(text)
    print("\nExtraction Result JSON:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
