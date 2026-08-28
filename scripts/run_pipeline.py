"""End-to-end analysis pipeline: ingest -> extract -> build graph -> analytics -> artifacts."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from backend.app.graph.alerts import (alert_layering, alert_night_bursts,
                                      alert_structuring, attach_risk,
                                      resolve_alert_persons)
from backend.app.graph.analytics import bridge_nodes, detect_communities, rank_influencers
from backend.app.graph.builder import NetworkBuilder
from backend.app.ingestion.loaders import (load_cdr, load_registry,
                                           load_transactions, parse_fir,
                                           parse_surveillance)
from backend.app.nlp.entity_extractor import EntityExtractor

DATA = BASE / "data" / "sample"
ARTIFACTS = BASE / "artifacts"


def run(data_dir: Path = DATA, out_dir: Path = ARTIFACTS) -> dict:
    t0 = time.time()
    registry = load_registry(data_dir / "registry.json")
    extractor = EntityExtractor(registry)
    builder = NetworkBuilder(registry)

    docs = []
    for fir_path in sorted((data_dir / "firs").glob("*.txt")):
        docs.append(parse_fir(fir_path))
    for note in parse_surveillance(data_dir / "surveillance.txt"):
        docs.append(note)

    total_entities = 0
    for doc in docs:
        ents = extractor.extract(doc["text"])
        total_entities += len(ents)
        doc["entities"] = ents
        builder.add_text_document(doc.get("fir_id") or doc["note_id"], ents,
                                  doc["source_type"])

    cdr_rows = load_cdr(data_dir / "cdr.csv")
    tx_rows = load_transactions(data_dir / "transactions.csv")
    builder.add_calls(cdr_rows)
    builder.add_transactions(tx_rows)

    G = builder.G
    P = builder.person_projection()

    influencers = rank_influencers(P)
    communities = detect_communities(P)
    bridges = bridge_nodes(P, communities)

    alerts = []
    alerts += alert_structuring(tx_rows)
    alerts += alert_layering(tx_rows)
    alerts += alert_night_bursts(cdr_rows)
    flagged = resolve_alert_persons(alerts, G)
    influencers = attach_risk(influencers, flagged)

    comm_of = {}
    for idx, comm in enumerate(communities):
        for node in comm:
            comm_of[node] = idx

    graph_export = to_cytoscape(G, comm_of)
    stats = builder.stats()
    stats.update({
        "documents_processed": len(docs),
        "entities_extracted": total_entities,
        "persons_in_projection": P.number_of_nodes(),
        "cdr_records": len(cdr_rows),
        "transaction_records": len(tx_rows),
        "runtime_seconds": round(time.time() - t0, 2),
    })

    analytics = {
        "stats": stats,
        "influencers": influencers,
        "communities": [
            {"id": i,
             "size": len(comm),
             "members": [{"node": n, "label": P.nodes[n].get("label", n)} for n in comm]}
            for i, comm in enumerate(communities)
        ],
        "bridges": bridges,
        "alerts": sorted(alerts, key=lambda a: {"high": 0, "medium": 1}.get(a["severity"], 2)),
    }

    out_dir.mkdir(exist_ok=True)
    (out_dir / "graph.json").write_text(json.dumps(graph_export))
    (out_dir / "analytics.json").write_text(json.dumps(analytics, indent=2))
    return analytics


def to_cytoscape(G, comm_of: dict) -> dict:
    elements = []
    for nid, attrs in G.nodes(data=True):
        data = {"id": nid, "label": attrs.get("label", nid), "kind": attrs.get("kind")}
        if attrs.get("role"):
            data["role"] = attrs["role"]
        if attrs.get("person_id"):
            data["person_id"] = attrs["person_id"]
        if nid in comm_of:
            data["community"] = comm_of[nid]
        elements.append({"data": data, "group": "nodes"})
    seen_pairs = set()
    for u, v, key, attrs in G.edges(keys=True, data=True):
        pair_key = (u, v, attrs.get("relation"))
        rev = (v, u, attrs.get("relation"))
        if pair_key in seen_pairs or rev in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        data = {
            "id": f"{u}|{key}|{v}",
            "source": u,
            "target": v,
            "relation": attrs.get("relation"),
            "count": attrs.get("count"),
            "night_count": attrs.get("night_count"),
            "amount_sum": attrs.get("amount_sum"),
            "docs": attrs.get("docs", []),
        }
        elements.append({"data": data, "group": "edges"})
    return {"elements": elements}


if __name__ == "__main__":
    result = run()
    print(f"Stats: {json.dumps(result['stats'], indent=2)}")
    print(f"\nTop influencers:")
    for row in result["influencers"][:8]:
        print(f"  #{row['rank']:>2} {row['label']:<18} score={row['score']:.3f} "
              f"risk={row['risk_level']}")
    print(f"\nCommunities: {[c['size'] for c in result['communities']]}")
    print(f"Bridges: {[b['label'] for b in result['bridges'][:5]]}")
    print(f"\nAlerts ({len(result['alerts'])}):")
    for a in result["alerts"]:
        print(f"  [{a['severity'].upper():6}] {a['title']}: {a['detail']}")
