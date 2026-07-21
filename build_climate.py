#!/usr/bin/env python3
"""
build_climate.py — coarse growing-season climate grid for the Suitability Map
=============================================================================

Bakes `climate.json`, a small regular lon/lat grid of a 0-100 "growing
conditions" score for Switzerland, derived from Growing Degree Days (GDD,
base 5 °C, Apr–Oct) averaged over two recent seasons. Free public source:
Open-Meteo ERA5 archive (no API key). Uses only the Python standard library.

    python3 build_climate.py                 # → climate.json (0.2° grid)
    python3 build_climate.py --step 0.15 --years 2021 2022 2023

The map loads climate.json (like cantons/bfs) and, for every parcel centroid,
reads the nearest grid cell as a weighted "Klima" factor in the score — works
in live mode too, since it's a bundled coarse grid (no per-parcel API calls).

GDD → score: linear ramp, 900 GDD → 0 (too cool for reliable arable),
2000 GDD → 100. A transparent heuristic, tune GDD_LO/GDD_HI as needed.
"""

import argparse, json, sys, time
from urllib.request import urlopen, Request
from urllib.parse import urlencode

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
# Switzerland bounding box (a little generous so edge parcels find a cell)
LON0, LON1 = 5.9, 10.6
LAT0, LAT1 = 45.8, 47.9
GDD_LO, GDD_HI = 900.0, 2000.0     # GDD(base 5) → 0..100 ramp
BASE_T = 5.0                        # GDD base temperature (°C)


def gdd_score(gdd):
    if gdd is None:
        return None
    return max(0, min(100, round(100 * (gdd - GDD_LO) / (GDD_HI - GDD_LO))))


def fetch_chunk(lats, lons, years):
    """Return list of mean growing-season GDD (base 5) per (lat,lon), averaged
    over `years`. One Open-Meteo call per year for the whole chunk."""
    per_year_sums = [ [] for _ in lats ]   # list of yearly GDD per location
    for y in years:
        q = {
            "latitude":  ",".join(f"{v:.4f}" for v in lats),
            "longitude": ",".join(f"{v:.4f}" for v in lons),
            "start_date": f"{y}-04-01", "end_date": f"{y}-10-31",
            "daily": "temperature_2m_mean", "timezone": "Europe/Zurich",
        }
        url = f"{ARCHIVE}?{urlencode(q)}"
        doc = None
        for attempt in range(6):
            try:
                req = Request(url, headers={"User-Agent": "sfr-climate-etl/1.0"})
                with urlopen(req, timeout=120) as r:
                    doc = json.loads(r.read().decode("utf-8"))
                break
            except Exception as ex:
                wait = 5 * (attempt + 1)
                print(f"    retry {attempt+1} after {wait}s ({ex})", file=sys.stderr)
                time.sleep(wait)
        if doc is None:
            raise RuntimeError("Open-Meteo request failed after retries")
        locs = doc if isinstance(doc, list) else [doc]
        for i, loc in enumerate(locs):
            temps = [t for t in loc.get("daily", {}).get("temperature_2m_mean", []) if t is not None]
            gdd = sum(max(0.0, t - BASE_T) for t in temps) if temps else None
            per_year_sums[i].append(gdd)
        time.sleep(0.3)  # be polite
    out = []
    for ys in per_year_sums:
        vals = [g for g in ys if g is not None]
        out.append(round(sum(vals) / len(vals)) if vals else None)
    return out


def frange(a, b, step):
    vals, v = [], a
    while v <= b + 1e-9:
        vals.append(round(v, 4)); v += step
    return vals


def main():
    ap = argparse.ArgumentParser(description="Bake a coarse GDD climate grid (climate.json).")
    ap.add_argument("--step", type=float, default=0.2, help="Grid step in degrees (default 0.2)")
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2023],
                    help="Seasons to average (default 2022 2023)")
    ap.add_argument("--out", default="climate.json")
    a = ap.parse_args()

    lons = frange(LON0, LON1, a.step)
    lats = frange(LAT0, LAT1, a.step)
    print(f"Grid {len(lons)}×{len(lats)} = {len(lons)*len(lats)} points, "
          f"years {a.years} …", file=sys.stderr)

    # flatten to a point list (row-major: index = j*nlon + i)
    pts = [(lo, la) for la in lats for lo in lons]
    scores, gdds = [], []
    CH = 25  # locations per Open-Meteo call (keep the weighted request small)
    for s in range(0, len(pts), CH):
        chunk = pts[s:s+CH]
        vals = fetch_chunk([la for _, la in chunk], [lo for lo, _ in chunk], a.years)
        gdds.extend(vals)
        scores.extend(gdd_score(v) for v in vals)
        print(f"  {min(s+CH, len(pts))}/{len(pts)} points", file=sys.stderr)
        time.sleep(1.0)  # spacing between chunks

    grid = {"lon0": LON0, "lat0": LAT0, "dlon": a.step, "dlat": a.step,
            "nlon": len(lons), "nlat": len(lats),
            "years": a.years, "base_t": BASE_T,
            "gdd_lo": GDD_LO, "gdd_hi": GDD_HI,
            "score": scores}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(grid, fh, separators=(",", ":"))

    ok = [s for s in scores if s is not None]
    print(f"\nWrote {a.out}  ({len(scores)} cells, {len(ok)} with data)", file=sys.stderr)
    if ok:
        print(f"Climate score: min={min(ok)} max={max(ok)} "
              f"(GDD ramp {GDD_LO:.0f}→{GDD_HI:.0f})", file=sys.stderr)
    print("→ Put climate.json next to parzellen-eignungskarte.html.", file=sys.stderr)


if __name__ == "__main__":
    main()
