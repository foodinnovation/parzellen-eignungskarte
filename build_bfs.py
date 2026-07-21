#!/usr/bin/env python3
"""
build_bfs.py — BFS regional-context extractor for the Parcel Suitability Map
============================================================================

Queries the Swiss Federal Statistical Office STAT-TAB PxWeb API (free, no auth)
and writes `bfs_cantons.json`, a small lookup the map loads to show regional
context per canton: share of organic farms, full-/part-time split, and the
canton's crop-area structure (arable vs grassland etc.).

    python3 build_bfs.py                 # → bfs_cantons.json
    python3 build_bfs.py --year 2024

Uses only the Python standard library. Run it on your machine (the BFS API is
reachable there); drop bfs_cantons.json next to parzellen-eignungskarte.html.

Table: px-x-0702000000_106  "Landwirtschaftliche Betriebe und LN auf
Klassifizierungsebene 3 nach Kanton, Produktionszone, Betriebssystem,
Betriebsform und Jahr".
"""

import argparse, json, sys
from urllib.request import urlopen, Request

API = "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0702000000_106/px-x-0702000000_106.px"

# BFS canton value-index (0..26) → 2-letter code, in the table's standard order.
CANTON_CODE = ["CH","ZH","BE","LU","UR","SZ","OW","NW","GL","ZG","FR","SO","BS",
               "BL","SH","AR","AI","SG","GR","AG","TG","TI","VD","VS","NE","GE","JU"]

def post(query):
    body = json.dumps(query).encode("utf-8")
    req = Request(API, data=body,
                  headers={"Content-Type": "application/json",
                           "User-Agent": "sfr-bfs-etl/1.0"})
    with urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

def q_year_index(year):
    # Jahr values run newest→oldest starting at 2025 = index "0".
    return str(2025 - int(year))

def query(beob, betriebssystem, betriebsform, year_idx):
    return {"query": [
        {"code": "Beobachtungseinheit", "selection": {"filter": "item", "values": beob}},
        {"code": "Kanton", "selection": {"filter": "all", "values": ["*"]}},
        {"code": "Landwirtschaftliche Produktionszone", "selection": {"filter": "item", "values": ["0"]}},
        {"code": "Betriebssystem", "selection": {"filter": "item", "values": betriebssystem}},
        {"code": "Betriebsform", "selection": {"filter": "item", "values": betriebsform}},
        {"code": "Jahr", "selection": {"filter": "item", "values": [year_idx]}},
    ], "response": {"format": "json-stat2"}}

def jsonstat_to_map(js, dim_of_interest):
    """Return {canton_code: {category_label: value}} from a json-stat2 doc,
    varying Kanton and `dim_of_interest`, with all other dims singletons."""
    dims = js["id"]; sizes = js["size"]
    cats = {d: js["dimension"][d]["category"] for d in dims}
    # index positions
    def order(dim):  # label list ordered by category index
        idx = cats[dim]["index"]
        lbl = cats[dim]["label"]
        inv = sorted(idx, key=lambda k: idx[k])
        return [(k, lbl[k]) for k in inv]
    values = js["value"]
    strides = [1]*len(dims)
    for i in range(len(dims)-2, -1, -1):
        strides[i] = strides[i+1]*sizes[i+1]
    kanton_i = dims.index("Kanton")
    doi_i = dims.index(dim_of_interest)
    kanton_items = order("Kanton")
    doi_items = order(dim_of_interest)
    out = {}
    base = [0]*len(dims)  # all other dims have size 1 → index 0
    for ci, (kkey, _) in enumerate(kanton_items):
        code = CANTON_CODE[ci] if ci < len(CANTON_CODE) else kkey
        rec = {}
        for di, (dkey, dlabel) in enumerate(doi_items):
            pos = list(base); pos[kanton_i] = ci; pos[doi_i] = di
            flat = sum(p*s for p, s in zip(pos, strides))
            v = values[flat] if flat < len(values) else None
            rec[dlabel] = v
        out[code] = rec
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="2025")
    ap.add_argument("--out", default="bfs_cantons.json")
    a = ap.parse_args()
    yi = q_year_index(a.year)

    print("Querying BFS: farms by Betriebssystem (organic/conventional) …", file=sys.stderr)
    sys_js = post(query(["0"], ["0", "1", "2"], ["0"], yi))          # Betriebe, Bio/Konv
    sys_map = jsonstat_to_map(sys_js, "Betriebssystem")

    print("Querying BFS: farms by Betriebsform (full/part-time) …", file=sys.stderr)
    form_js = post(query(["0"], ["0"], ["0", "1", "2"], yi))         # Betriebe, Haupt/Neben
    form_map = jsonstat_to_map(form_js, "Betriebsform")

    print("Querying BFS: land-use structure (arable vs grassland, ha) …", file=sys.stderr)
    # Beobachtungseinheit: 1 = LN Total, 37 = Kunstwiesen, 38 = Weiden,
    # 39-42 grassland; arable ≈ Total − grassland. We fetch Total + a few.
    lu_js = post(query(["1", "37", "38", "39", "40", "42"], ["0"], ["0"], yi))
    lu_map = jsonstat_to_map(lu_js, "Beobachtungseinheit")

    out = {}
    for code in CANTON_CODE:
        s = sys_map.get(code, {}); f = form_map.get(code, {}); lu = lu_map.get(code, {})
        total = next((v for k, v in s.items() if "Total" in k), None)
        bio = next((v for k, v in s.items() if "Bio" in k), None)
        haupt = next((v for k, v in f.items() if "Hauptberufl" in k), None)
        neben = next((v for k, v in f.items() if "Nebenberufl" in k), None)
        ln_total = next((v for k, v in lu.items() if "Total" in k), None)
        grass = sum(v for k, v in lu.items()
                    if v is not None and ("wiese" in k.lower() or "weide" in k.lower()))
        out[code] = {
            "betriebe": total,
            "bio_share": round(100*bio/total, 1) if (bio and total) else None,
            "haupt": haupt, "neben": neben,
            "haupt_share": round(100*haupt/(haupt+neben), 1) if (haupt and neben) else None,
            "ln_ha": ln_total,
            "gruenland_ha": round(grass) if grass else None,
            "gruenland_share": round(100*grass/ln_total, 1) if (grass and ln_total) else None,
            "year": a.year,
        }

    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"\nWrote {a.out} for {len([c for c in out if out[c]['betriebe']])} cantons.",
          file=sys.stderr)
    ch = out.get("CH", {})
    print(f"Sanity (CH {a.year}): {ch.get('betriebe')} farms, "
          f"{ch.get('bio_share')}% organic, {ch.get('gruenland_share')}% grassland of LN.",
          file=sys.stderr)

if __name__ == "__main__":
    main()
