from __future__ import annotations

from datetime import datetime

import networkx as nx

NIGHT_HOURS = set(range(0, 6))
STRUCTURING_AMOUNT = 50000.0


def alert_structuring(tx_rows: list[dict]) -> list[dict]:
    by_acc: dict[str, list[dict]] = {}
    for row in tx_rows:
        if row["mode"] != "cash_deposit":
            continue
        amt = float(row["amount_inr"])
        if not (0.90 * STRUCTURING_AMOUNT <= amt <= STRUCTURING_AMOUNT):
            continue
        by_acc.setdefault(row["to_account"], []).append(row)
    alerts = []
    for acc, rows in by_acc.items():
        days = sorted({r["timestamp"][:10] for r in rows})
        span = (datetime.fromisoformat(days[-1]) - datetime.fromisoformat(days[0])).days
        total = sum(float(r["amount_inr"]) for r in rows)
        if len(rows) >= 5 and span <= 7:
            alerts.append({
                "type": "structuring",
                "severity": "high",
                "title": f"Structuring pattern into {acc}",
                "detail": (f"{len(rows)} cash deposits of ~Rs.{STRUCTURING_AMOUNT:,.0f} across "
                           f"{len(days)} day(s) — total Rs.{total:,.0f}, kept below reporting threshold."),
                "accounts": [acc],
                "evidence": [{"timestamp": r["timestamp"], "amount_inr": r["amount_inr"]} for r in rows],
            })
    return alerts


def alert_layering(tx_rows: list[dict], max_hours: float = 24.0,
                   retention: float = 0.8) -> list[dict]:
    rows = sorted(
        (r for r in tx_rows if r["from_account"] != "CASH" and r["to_account"] != "CASH"),
        key=lambda r: datetime.fromisoformat(r["timestamp"]),
    )
    chains: list[dict] = []
    used: set[int] = set()

    def ratio(a: float, b: float) -> float:
        return b / max(a, 1e-9)

    for i in range(len(rows)):
        if i in used:
            continue
        first = rows[i]
        t1 = datetime.fromisoformat(first["timestamp"])
        a1 = float(first["amount_inr"])
        if a1 < 25000:
            continue
        hops = None
        for j in range(i + 1, len(rows)):
            second = rows[j]
            t2 = datetime.fromisoformat(second["timestamp"])
            if (t2 - t1).total_seconds() / 3600 > max_hours:
                break
            if second["from_account"] == first["to_account"] and \
                    retention <= ratio(a1, float(second["amount_inr"])) <= 1.05:
                hops = [first, second]
                used.update({i, j})
                k = j
                while True:
                    nxt = _next_hop(rows, used, hops, k, max_hours, retention)
                    if nxt is None:
                        break
                    m_idx, cand = nxt
                    hops.append(cand)
                    used.add(m_idx)
                    k = m_idx
                break
        if hops:
            accounts = [h["from_account"] for h in hops] + [hops[-1]["to_account"]]
            chains.append({
                "type": "layering",
                "severity": "high" if len(hops) >= 3 else "medium",
                "title": "Rapid multi-hop fund movement",
                "detail": (f"{len(hops)}-hop chain {' → '.join(accounts)} moved "
                           f"Rs.{float(hops[-1]['amount_inr']):,.0f} within {max_hours:.0f}h of receipt."),
                "accounts": list(dict.fromkeys(accounts)),
                "evidence": [{"timestamp": h["timestamp"], "from": h["from_account"],
                              "to": h["to_account"], "amount_inr": h["amount_inr"]} for h in hops],
            })
    return chains


def _next_hop(rows, used, hops, k, max_hours, retention):
    last_time = datetime.fromisoformat(hops[-1]["timestamp"])
    last_amt = float(hops[-1]["amount_inr"])
    for m in range(k + 1, len(rows)):
        cand = rows[m]
        tc = datetime.fromisoformat(cand["timestamp"])
        if (tc - last_time).total_seconds() / 3600 > max_hours:
            return None
        if m in used:
            continue
        if cand["from_account"] == hops[-1]["to_account"]:
            r = float(cand["amount_inr"]) / max(last_amt, 1e-9)
            if retention <= r <= 1 / retention:
                return m, cand
    return None


def alert_night_bursts(cdr_rows: list[dict], min_calls: int = 8,
                       min_fraction: float = 0.4) -> list[dict]:
    pairs: dict[tuple[str, str], dict] = {}
    for row in cdr_rows:
        hour = int(row["timestamp"][11:13])
        key = tuple(sorted((row["caller_number"], row["callee_number"])))
        d = pairs.setdefault(key, {"count": 0, "night": 0})
        d["count"] += 1
        if hour in NIGHT_HOURS:
            d["night"] += 1
    alerts = []
    for (a, b), d in sorted(pairs.items(), key=lambda kv: (-kv[1]["night"], -kv[1]["count"])):
        frac = d["night"] / d["count"]
        if d["count"] >= min_calls and frac >= min_fraction:
            alerts.append({
                "type": "night_call_burst",
                "severity": "medium",
                "title": f"Nocturnal contact burst {a} ↔ {b}",
                "detail": (f"{d['count']} calls between this pair; {d['night']} ({frac:.0%}) between "
                           f"00:00–05:00 — consistent with conspiracy communication discipline."),
                "phones": [a, b],
                "evidence": {"total_calls": d["count"], "night_calls": d["night"]},
            })
    return alerts


def resolve_alert_persons(alerts: list[dict], G: nx.MultiDiGraph) -> dict[str, int]:
    """Map each alert's assets to owning persons; returns person_id -> alert_count."""
    flagged: dict[str, int] = {}
    owner_of = {}
    for u, v, data in G.edges(data=True):
        rel = str(data.get("relation", ""))
        if rel.startswith("OWNS"):
            owner_of[v] = u
    weight = {"high": 2, "medium": 1, "low": 0}
    for alert in alerts:
        persons = set()
        for field in ("accounts", "phones"):
            for val in alert.get(field, []):
                nid = f"{field[:-1] if field.endswith('s') else field}:{str(val).lower()}"
                if nid in owner_of:
                    persons.add(owner_of[nid])
        for pid in persons:
            flagged[pid] = flagged.get(pid, 0) + weight.get(alert["severity"], 1)
    return flagged


def attach_risk(influencers: list[dict], flagged_points: dict[str, int]) -> list[dict]:
    for row in influencers:
        pts = flagged_points.get(row["node"], 0)
        row["risk_points"] = pts
        row["risk_level"] = "critical" if pts >= 4 else ("elevated" if pts >= 1 else "baseline")
        row["score"] = round(min(row["score"] * (1 + 0.15 * pts), 1.0), 4)
    influencers.sort(key=lambda r: -r["score"])
    for i, row in enumerate(influencers, 1):
        row["rank"] = i
    return influencers
