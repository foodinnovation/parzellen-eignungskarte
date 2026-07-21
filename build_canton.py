#!/usr/bin/env python3
"""
build_canton.py — Phase 2 ETL for the Swiss Parcel Suitability Map
==================================================================

Pulls one canton's agricultural parcels from the public geodienste.ch
OGC API Features service, classifies each parcel's current crop, computes a
0-100 "mixed-crop adoption" suitability score, and writes a GeoJSON file
(`parcels_scored.geojson`) that the map (parzellen-eignungskarte.html) loads
directly — drop it in the same folder as the HTML.

WHY A LOCAL SCRIPT:  the parcel service is fetched from your machine, where
network access to geodienste.ch is unrestricted. The output is a plain static
GeoJSON, so hosting stays a simple static file drop.

--------------------------------------------------------------------
CORE PATH (no extra installs, uses only the Python standard library):
    python3 build_canton.py --canton AG
    python3 build_canton.py --canton SO --out solothurn.geojson

OPTIONAL TERRAIN/SOIL ENRICHMENT (needs geopandas + rasterio + rasterstats):
    # soil suitability polygons  (download the BLW "Bodeneignung Kulturland"
    #   GeoPackage/Shapefile from opendata.swiss first)
    # dem  = a swissALTI3D / DHM GeoTIFF covering the canton
    python3 build_canton.py --canton AG \
        --soil bodeneignung_kulturland.gpkg \
        --dem  swissalti3d_ag.tif

When --soil / --dem are given, each parcel additionally receives:
    soil_score (0-100), slope (%), elev (m)   → folded into the final score
    and the map's Hangneigung/Höhe sliders then filter these parcels for real.
--------------------------------------------------------------------
"""

import argparse, json, sys, gzip, io, time
from urllib.request import urlopen, Request
from urllib.parse import urlencode

OGC = "https://geodienste.ch/db/lwb_nutzungsflaechen_v2_0_0/deu/ogcapi"
COLLECTION = "nutzungsflaechen"

# Approximate WGS84 bounding boxes (minLon, minLat, maxLon, maxLat) for
# fetching. Add cantons as needed; only openly-accessible cantons make sense.
CANTON_BBOX = {
    "AG": (7.71, 47.13, 8.46, 47.62), "SO": (7.34, 47.06, 8.01, 47.50),
    "BE": (6.86, 46.32, 8.47, 47.35), "ZH": (8.36, 47.16, 8.98, 47.69),
    "LU": (7.83, 46.78, 8.51, 47.29), "TG": (8.66, 47.44, 9.55, 47.70),
    "SG": (8.79, 46.87, 9.68, 47.55), "FR": (6.74, 46.44, 7.36, 47.02),
    "VD": (6.06, 46.19, 7.25, 46.99), "BL": (7.33, 47.35, 7.97, 47.56),
    "SH": (8.40, 47.58, 8.90, 47.81), "ZG": (8.42, 47.08, 8.71, 47.25),
    "GR": (8.66, 46.17, 10.49, 47.06), "AR": (9.24, 47.24, 9.68, 47.49),
    "AI": (9.28, 47.24, 9.62, 47.42), "GL": (8.85, 46.80, 9.33, 47.18),
    "JU": (6.87, 47.19, 7.56, 47.50), "NW": (8.24, 46.80, 8.68, 47.02),
    "OW": (8.07, 46.72, 8.55, 46.96), "UR": (8.40, 46.53, 9.02, 46.98),
    "VS": (6.77, 45.86, 8.48, 46.65), "SZ": (8.43, 46.88, 9.11, 47.21),
}

# ------------------------- crop classification -------------------------
# Mirrors the JavaScript classifier in the HTML. Primary key = lnf_code range;
# German-text keywords override fodder crops that sit on arable land.
FODDER_KW = ("silomais", "grünmais", "gruenmais", "silo- und",
             "futterrübe", "futterrube", "futterrüben")
GRASS_KW  = ("wiese", "weide", "weiden", "grünfläche", "gruenflaeche",
             "streue", "sömmerung", "soemmerung")

def classify(props):
    try:
        code = int(props.get("lnf_code"))
    except (TypeError, ValueError):
        code = -1
    n = (props.get("nutzung") or "").lower()
    is_fodder = any(k in n for k in FODDER_KW)
    if (600 <= code <= 699) or any(k in n for k in GRASS_KW):
        return "grassland", 5, True
    if 400 <= code <= 599:
        return ("fodder", 20, True) if is_fodder else ("arable", 85, False)
    if 700 <= code <= 799:
        return "permanent", 35, False
    if is_fodder:
        return "fodder", 20, True
    return "other", 12, False

def base_score(props, soil_score=None):
    cat, base, live = classify(props)
    score = base if soil_score is None else round(0.6*base + 0.4*soil_score)
    return cat, max(0, min(100, int(score))), live

# ------------------------- fetching (stdlib) -------------------------
def fetch_json(url):
    req = Request(url, headers={"Accept": "application/geo+json,application/json",
                                "User-Agent": "sfr-parcel-etl/1.0"})
    with urlopen(req, timeout=120) as r:
        raw = r.read()
        if r.info().get("Content-Encoding") == "gzip":
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return json.loads(raw.decode("utf-8"))

def next_link(doc):
    for l in doc.get("links", []):
        if l.get("rel") == "next":
            return l.get("href")
    return None

def fetch_parcels(canton, bbox, page=2000, max_features=None):
    q = {"f": "json", "limit": page, "bbox": ",".join(f"{c:.5f}" for c in bbox)}
    url = f"{OGC}/collections/{COLLECTION}/items?{urlencode(q)}"
    feats, page_no = [], 0
    while url:
        page_no += 1
        doc = fetch_json(url)
        got = doc.get("features", [])
        # keep only parcels whose attribute canton matches (bbox overlaps neighbours)
        for f in got:
            p = f.get("properties", {})
            # keep parcels of this canton; drop overlapping biodiversity features
            if (p.get("kanton") or "").upper() == canton and \
               str(p.get("ist_ueberlagernd")).lower() != "true":
                feats.append(f)
        print(f"  page {page_no}: +{len(got)} fetched, {len(feats)} in {canton}",
              file=sys.stderr)
        if max_features and len(feats) >= max_features:
            break
        url = next_link(doc)
        time.sleep(0.2)  # be polite
    return feats

# ------------------------- optional enrichment -------------------------
def enrich(features, soil_path, dem_path):
    """Spatial-join soil suitability and sample slope/elevation from a DEM.
    Requires geopandas, rasterio, rasterstats, numpy. Runs only if paths given."""
    import geopandas as gpd
    from shapely.geometry import shape
    import numpy as np, rasterio
    from rasterio.warp import transform_geom

    gdf = gpd.GeoDataFrame(
        [{**f["properties"], "geometry": shape(f["geometry"])} for f in features],
        crs="EPSG:4326")

    # --- soil suitability polygons → categorical 0-100 ---
    if soil_path:
        soil = gpd.read_file(soil_path).to_crs("EPSG:4326")
        # BLW "eignungsei" text → coarse suitability for arable cropping
        def soil_to_score(t):
            t = (t or "").lower()
            if "acker" in t: return 90
            if "getreide" in t or "hackfrucht" in t: return 70
            if "futter" in t: return 40
            return 10
        soil["soil_score"] = soil.get("eignungsei", "").map(soil_to_score) \
            if "eignungsei" in soil else 50
        joined = gpd.sjoin(gdf, soil[["soil_score", "geometry"]],
                           predicate="intersects", how="left")
        joined = joined[~joined.index.duplicated(keep="first")]
        # reindex to gdf's row index so values line up even if sjoin reordered/dropped rows
        gdf["soil_score"] = joined["soil_score"].reindex(gdf.index).fillna(50).values

    # --- slope (%) and elevation (m) from DEM ---
    if dem_path:
        with rasterio.open(dem_path) as src:
            cent = gdf.geometry.centroid
            elevs, slopes = [], []
            arr = src.read(1).astype("float32")
            gy, gx = np.gradient(arr, src.res[1], src.res[0])
            slope_pct = np.hypot(gx, gy) * 100.0
            for pt in cent:
                g = transform_geom("EPSG:4326", src.crs,
                                   {"type": "Point", "coordinates": [pt.x, pt.y]})
                x, y = g["coordinates"]
                try:
                    row, col = src.index(x, y)
                    elevs.append(float(arr[row, col]))
                    slopes.append(float(slope_pct[row, col]))
                except Exception:
                    elevs.append(None); slopes.append(None)
            gdf["elev"] = elevs
            gdf["slope"] = slopes

    # write enriched values back onto the features
    for f, (_, row) in zip(features, gdf.iterrows()):
        for k in ("soil_score", "slope", "elev"):
            if k in gdf.columns and row.get(k) is not None:
                f["properties"][k] = None if (isinstance(row[k], float) and row[k] != row[k]) else row[k]
    return features

# ------------------------- main -------------------------
def main():
    ap = argparse.ArgumentParser(description="Build a scored parcel GeoJSON for one canton.")
    ap.add_argument("--canton", required=True, help="Canton code, e.g. AG, SO, BE")
    ap.add_argument("--out", default="parcels_scored.geojson")
    ap.add_argument("--bbox", help="Override bbox 'minLon,minLat,maxLon,maxLat'")
    ap.add_argument("--max", type=int, default=None, help="Cap number of parcels (testing)")
    ap.add_argument("--soil", help="Path to BLW Bodeneignung polygons (gpkg/shp)")
    ap.add_argument("--dem", help="Path to DEM GeoTIFF (swissALTI3D/DHM) for slope+elev")
    a = ap.parse_args()

    canton = a.canton.upper()
    bbox = tuple(float(x) for x in a.bbox.split(",")) if a.bbox else CANTON_BBOX.get(canton)
    if not bbox:
        sys.exit(f"No bbox for {canton}. Pass --bbox minLon,minLat,maxLon,maxLat.")

    print(f"Fetching parcels for {canton} …", file=sys.stderr)
    feats = fetch_parcels(canton, bbox, max_features=a.max)
    print(f"Collected {len(feats)} parcels.", file=sys.stderr)

    if a.soil or a.dem:
        print("Enriching with soil / terrain …", file=sys.stderr)
        try:
            feats = enrich(feats, a.soil, a.dem)
        except ImportError as e:
            print(f"  (skipped enrichment — install geopandas/rasterio/rasterstats: {e})",
                  file=sys.stderr)

    # score
    stats = {"arable": 0, "grassland": 0, "fodder": 0, "permanent": 0, "other": 0}
    for f in feats:
        p = f["properties"]
        cat, score, live = base_score(p, p.get("soil_score"))
        p["_cat"] = cat
        p["score"] = score
        p["excluded"] = bool(live)          # default: livestock/grassland excluded
        stats[cat] = stats.get(cat, 0) + 1

    fc = {"type": "FeatureCollection", "features": feats}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False)
    print(f"\nWrote {a.out}  ({len(feats)} parcels)", file=sys.stderr)
    print("Crop mix: " + ", ".join(f"{k}={v}" for k, v in stats.items() if v),
          file=sys.stderr)
    print("→ Put it next to parzellen-eignungskarte.html and reload.", file=sys.stderr)

if __name__ == "__main__":
    main()
