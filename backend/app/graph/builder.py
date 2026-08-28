from __future__ import annotations

import networkx as nx

NIGHT_HOURS = set(range(0, 6))


def _nid(kind: str, value: str) -> str:
    return f"{kind}:{str(value).strip().lower()}"


class NetworkBuilder:
    """Builds a multi-source knowledge graph.

    Node kinds: person, phone, account, vehicle, location, org
    Edge kinds: OWNS_*, CALLS, TRANSACTED, CO_OCCURS, LINKED_TO
    """

    def __init__(self, registry: dict):
        self.G = nx.MultiDiGraph()
        self.registry = registry
        self._add_registry_entities()

    def _add_person(self, pid: str, label: str, role: str | None = None):
        self._add_node(_nid("person", pid), kind="person", label=label,
                       person_id=pid, role=role)

    def _add_node(self, nid: str, **attrs):
        if not self.G.has_node(nid):
            self.G.add_node(nid, **attrs)

    def _ensure_location(self, name: str) -> str:
        nid = _nid("location", name.title())
        self._add_node(nid, kind="location", label=name.title())
        return nid

    def _add_registry_entities(self):
        for pid, p in self.registry["persons"].items():
            self._add_person(pid, p["name"], p.get("role"))
            for ph in p["phones"]:
                nid = _nid("phone", ph)
                self._add_node(nid, kind="phone", label=f"+91 {ph}")
                self._link_owner(pid, nid, "OWNS_PHONE")
            for acc in p["accounts"]:
                nid = _nid("account", acc)
                self._add_node(nid, kind="account", label=acc)
                self._link_owner(pid, nid, "OWNS_ACCOUNT")
        for plate, pid in self.registry.get("vehicles", {}).items():
            if not plate:
                continue
            nid = _nid("vehicle", plate)
            self._add_node(nid, kind="vehicle", label=plate)
            if pid:
                self._link_owner(pid, nid, "OWNS_VEHICLE")
        for loc in self.registry.get("locations", []):
            self._ensure_location(loc)

    def _link_owner(self, pid: str, asset_nid: str, rel: str):
        self.G.add_edge(_nid("person", pid), asset_nid, key=rel, relation=rel)

    def add_calls(self, cdr_rows: list[dict]):
        agg: dict[tuple[str, str], dict] = {}
        for row in cdr_rows:
            a, b = row["caller_number"], row["callee_number"]
            if a == b:
                continue
            hour = int(row["timestamp"][11:13])
            key = tuple(sorted((a, b)))
            d = agg.setdefault(key, {"count": 0, "total_duration": 0, "night_count": 0})
            d["count"] += 1
            d["total_duration"] += int(row["duration_sec"])
            if hour in NIGHT_HOURS:
                d["night_count"] += 1
        for (a, b), d in agg.items():
            na, nb = _nid("phone", a), _nid("phone", b)
            self._add_node(na, kind="phone", label=f"+91 {a}")
            self._add_node(nb, kind="phone", label=f"+91 {b}")
            self.G.add_edge(na, nb, key="CALLS", relation="CALLS",
                            count=d["count"], total_duration=d["total_duration"],
                            night_count=d["night_count"])
            self.G.add_edge(nb, na, key="CALLED_BY", relation="CALLED_BY",
                            count=d["count"], total_duration=d["total_duration"],
                            night_count=d["night_count"])

    def add_transactions(self, tx_rows: list[dict]):
        agg: dict[tuple[str, str], dict] = {}
        for row in tx_rows:
            a, b = row["from_account"], row["to_account"]
            if a == b or a == "CASH" or b == "CASH":
                continue
            key = (a, b)
            d = agg.setdefault(key, {"count": 0, "amount_sum": 0.0})
            d["count"] += 1
            d["amount_sum"] += float(row["amount_inr"])
        for (a, b), d in agg.items():
            na, nb = _nid("account", a), _nid("account", b)
            self._add_node(na, kind="account", label=a)
            self._add_node(nb, kind="account", label=b)
            self.G.add_edge(na, nb, key="TRANSACTED", relation="TRANSACTED",
                            amount_sum=round(d["amount_sum"], 2), count=d["count"])

    def add_text_document(self, doc_id: str, entities: list[dict], doc_type: str):
        persons, locations = [], []
        phones, vehicles = [], []
        seen_locations = set()
        for ent in entities:
            etype, value, cid = ent["type"], ent["value"], ent.get("canonical_id")
            if etype == "person":
                pid = cid or str(value).strip().lower()
                self._ensure_person_node(pid)
                persons.append(pid)
            elif etype == "location":
                loc_nid = self._ensure_location(value)
                if loc_nid not in seen_locations:
                    seen_locations.add(loc_nid)
                    locations.append(loc_nid)
            elif etype == "phone":
                phones.append(str(value))
            elif etype == "vehicle":
                vehicles.append(str(value))

        uniq = list(dict.fromkeys(persons))
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                a, b = sorted((_nid("person", uniq[i]), _nid("person", uniq[j])))
                if a == b:
                    continue
                if self.G.has_edge(a, b, key="CO_OCCURS"):
                    docs = self.G[a][b]["CO_OCCURS"].get("docs", [])
                    docs.append(doc_id)
                    self.G[a][b]["CO_OCCURS"]["docs"] = docs
                    self.G[a][b]["CO_OCCURS"]["doc_types"].append(doc_type)
                else:
                    self.G.add_edge(a, b, key="CO_OCCURS", relation="CO_OCCURS",
                                    docs=[doc_id], doc_types=[doc_type])

        for pid in uniq:
            pn = _nid("person", pid)
            for lnid in locations:
                self._merge_doc_link(pn, lnid, doc_id)
            for ph in phones:
                owner = self.registry.get("phones_index", {}).get(ph)
                if owner and owner != pid:
                    self._merge_doc_link(pn, _nid("phone", ph), doc_id)
            for vh in vehicles:
                self._merge_doc_link(pn, _nid("vehicle", vh), doc_id)

    def _ensure_person_node(self, key: str):
        nid = _nid("person", key)
        if not self.G.has_node(nid):
            known = self.registry["persons"].get(key)
            label = known["name"] if known else str(key).title()
            role = (known or {}).get("role", "unresolved_mention")
            self.G.add_node(nid, kind="person", label=label, person_id=key,
                            role=role, discovered=known is None)

    def _merge_doc_link(self, src: str, dst: str, doc_id: str):
        if src == dst or not self.G.has_node(dst):
            return
        if self.G.has_edge(src, dst, key="LINKED_TO"):
            docs = self.G[src][dst]["LINKED_TO"]["docs"]
            if doc_id not in docs:
                docs.append(doc_id)
        else:
            self.G.add_edge(src, dst, key="LINKED_TO", relation="LINKED_TO", docs=[doc_id])

    def person_projection(self) -> nx.Graph:
        """Project persons connected through assets, co-occurrence and money/calls."""
        P = nx.Graph()
        for n, attrs in self.G.nodes(data=True):
            if attrs.get("kind") == "person":
                P.add_node(n, **attrs)

        def bump(a: str, b: str, w: float, reason: str):
            if a == b or not (P.has_node(a) and P.has_node(b)):
                return
            if not P.has_edge(a, b):
                P.add_edge(a, b, weight=0.0, reasons={})
            P[a][b]["weight"] += w
            P[a][b]["reasons"].setdefault(reason, 0)
            P[a][b]["reasons"][reason] += w

        for u, v, data in self.G.edges(data=True):
            rel = data.get("relation")
            pu = self.owner_of(u)
            pv = self.owner_of(v)
            if rel in ("CALLS", "CALLED_BY") and pu and pv:
                bump(pu, pv, data.get("count", 1) / 10.0 + 0.15 * data.get("night_count", 0), "calls")
            elif rel == "CO_OCCURS":
                bump(u, v, 1.0, "documented_together")
            elif rel == "TRANSACTED" and pu and pv:
                bump(pu, pv, min(data.get("amount_sum", 0) / 100000.0, 3.0), "money_flow")

        for a, b in P.edges():
            P[a][b]["weight"] = round(P[a][b]["weight"], 3)
        return P

    def owner_of(self, node_id: str) -> str | None:
        attrs = self.G.nodes.get(node_id, {})
        if attrs.get("kind") == "person":
            return node_id
        owners = [u for u, _, d in self.G.in_edges(node_id, data=True)
                  if str(d.get("relation", "")).startswith("OWNS")]
        return owners[0] if owners else None

    def stats(self) -> dict:
        kinds: dict[str, int] = {}
        rels: dict[str, int] = {}
        for _, attrs in self.G.nodes(data=True):
            kinds[attrs.get("kind", "?")] = kinds.get(attrs.get("kind", "?"), 0) + 1
        for _, _, attrs in self.G.edges(data=True):
            rels[attrs.get("relation", "?")] = rels.get(attrs.get("relation", "?"), 0) + 1
        return {"nodes": self.G.number_of_nodes(), "edges": self.G.number_of_edges(),
                "node_kinds": kinds, "edge_relations": rels}
