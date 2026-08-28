from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..ingestion.loaders import load_registry

BASE = Path(__file__).resolve().parents[3]
ARTIFACTS = BASE / "artifacts"
DATA = BASE / "data" / "sample"

router = APIRouter(prefix="/api")


def _load(name: str) -> dict:
    path = ARTIFACTS / name
    if not path.exists():
        raise HTTPException(503, f"Artifact {name} missing — run scripts/run_pipeline.py first")
    return json.loads(path.read_text())


@lru_cache(maxsize=4)
def _cached(name: str, mtime: float) -> dict:
    return _load(name)


def _fresh(name: str) -> dict:
    path = ARTIFACTS / name
    if not path.exists():
        raise HTTPException(503, f"Artifact {name} missing — run scripts/run_pipeline.py first")
    return _cached(name, path.stat().st_mtime)


@router.get("/graph")
def graph() -> dict:
    return _fresh("graph.json")


@router.get("/analytics")
def analytics() -> dict:
    return _fresh("analytics.json")


@router.get("/stats")
def stats() -> dict:
    return _fresh("analytics.json")["stats"]


@router.get("/person/{node_id:path}")
def person(node_id: str) -> dict:
    g = _fresh("graph.json")
    a = _fresh("analytics.json")
    reg = load_registry(DATA / "registry.json")
    node = next((n["data"] for n in g["elements"] if n["group"] == "nodes"
                 and n["data"]["id"] == node_id), None)
    if node is None:
        raise HTTPException(404, f"Unknown entity {node_id}")

    pid = node.get("person_id")
    owned: set[str] = set()
    if pid:
        p = reg["persons"].get(pid, {})
        owned = {a.lower() for a in (*p.get("phones", []), *p.get("accounts", []))}

    edges = [e["data"] for e in g["elements"] if e["group"] == "edges"
             and (e["data"]["source"] == node_id or e["data"]["target"] == node_id)]
    label_of = {n["data"]["id"]: n["data"]["label"] for n in g["elements"]
                if n["group"] == "nodes"}
    neighbors = []
    for e in edges:
        other = e["target"] if e["source"] == node_id else e["source"]
        neighbors.append({
            "id": other, "label": label_of.get(other, other),
            "relation": e.get("relation"),
            "count": e.get("count"), "amount_sum": e.get("amount_sum"),
            "docs": e.get("docs", []),
        })
    rank = next((r for r in a["influencers"] if r["node"] == node_id), None)
    related_alerts = [al for al in a["alerts"]
                      if owned & {str(v).lower() for field in ("accounts", "phones")
                                  for v in al.get(field, [])}]
    return {
        "entity": node,
        "influence": rank,
        "neighbors": sorted(neighbors, key=lambda n: -(n["count"] or 0)),
        "related_alerts": related_alerts,
    }


@router.get("/registry")
def registry() -> dict:
    return load_registry(DATA / "registry.json")
