from __future__ import annotations

import networkx as nx


def _norm(values: dict) -> dict:
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if hi - lo < 1e-9:
        return {k: 0.0 for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def rank_influencers(P: nx.Graph, top_n: int | None = None) -> list[dict]:
    if P.number_of_nodes() == 0:
        return []
    pr = nx.pagerank(P, weight="weight")
    btw = nx.betweenness_centrality(P, weight="weight")
    deg = {n: float(d) for n, d in P.degree()}
    pr_n, btw_n, deg_n = _norm(pr), _norm(btw), _norm(deg)
    ranked = []
    for node in P.nodes():
        score = 0.45 * pr_n[node] + 0.35 * btw_n[node] + 0.20 * deg_n[node]
        ranked.append({
            "node": node,
            "label": P.nodes[node].get("label", node),
            "role": P.nodes[node].get("role"),
            "score": round(score, 4),
            "pagerank": round(pr[node], 5),
            "betweenness": round(btw[node], 5),
            "degree": int(deg[node]),
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    for i, row in enumerate(ranked, 1):
        row["rank"] = i
    return ranked[:top_n] if top_n else ranked


def detect_communities(P: nx.Graph) -> list[list[str]]:
    if P.number_of_nodes() == 0:
        return []
    comms = nx.community.louvain_communities(P, weight="weight", seed=42)
    return [sorted(c) for c in sorted(comms, key=len, reverse=True)]


def bridge_nodes(P: nx.Graph, communities: list[list[str]], min_comm_size: int = 3) -> list[dict]:
    comm_of: dict[str, int] = {}
    for idx, comm in enumerate(communities):
        for node in comm:
            comm_of[node] = idx
    sizes = {idx: len(comm) for idx, comm in enumerate(communities)}
    out = []
    for node in P.nodes():
        if P.degree(node) < 2:
            continue
        spans = {comm_of.get(nb, -1) for nb in P.neighbors(node)}
        spans = {c for c in spans - {-1} if sizes.get(c, 0) >= min_comm_size}
        if len(spans) >= 2:
            out.append({
                "node": node,
                "label": P.nodes[node].get("label", node),
                "role": P.nodes[node].get("role"),
                "bridged_communities": len(spans),
                "degree": P.degree(node),
            })
    out.sort(key=lambda r: (-r["bridged_communities"], -r["degree"]))
    return out


def community_labels(P: nx.Graph, communities: list[list[str]]) -> dict[int, str]:
    labels = {}
    for idx, comm in enumerate(communities):
        members = [P.nodes[n].get("label", n) for n in comm]
        labels[idx] = ", ".join(members[:3]) + ("…" if len(members) > 3 else "")
    return labels
