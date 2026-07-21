#!/usr/bin/env python3
"""
build_mills.py — geocode Swiss grain mills → mills.geojson
==========================================================

Turns the member directory of the Dachverband Schweizerischer Müller (DSM /
Fédération des Meuniers Suisses) into a point layer for the map. The DSM
members cover >96 % of Swiss soft-wheat milling, so this is effectively the
national set of commercial grain mills. Source (public member directory):
https://www.dsm-fms.ch/verband/mitglieder/  (retrieved 2026-07).

Geocoding: geo.admin.ch SearchServer (free, no key) on "PLZ Ort", with
fallbacks. Town/postcode-level precision (no street numbers in the directory).
Uses only the Python standard library.

    python3 build_mills.py                 # → mills.geojson

Re-run to refresh if the directory changes. Drop mills.geojson next to the HTML.
"""

import json, sys, time
from urllib.request import urlopen, Request
from urllib.parse import urlencode

# (name, plz, ort) — DSM member mills
MILLS = [
    ("Aeschlimann-Mühle AG", "4932", "Lotzwil"),
    ("Bachtalmühle AG", "5643", "Sins"),
    ("Beck & Cie AG (Mühle Landshut)", "3427", "Utzenstorf"),
    ("Brunner AG (Mühle Oberembrach)", "8425", "Oberembrach"),
    ("Graf Mühle", "4464", "Maisprach"),
    ("Groupe Minoteries SA", "1523", "Granges-près-Marnand"),
    ("Grotzenmühle GmbH", "8840", "Einsiedeln"),
    ("Haldemann Mühle AG", "3555", "Trubschachen"),
    ("Kentaur AG", "3432", "Lützelflüh"),
    ("Knecht Mühle AG", "5325", "Leibstadt"),
    ("Landi Gros-de-Vaud (Moulin d'Echallens)", "1040", "Echallens"),
    ("Lehmann Alb. Lindmühle AG", "5413", "Birmenstorf"),
    ("Luginbühl Christian (Mühle Hindelbank)", "3324", "Hindelbank"),
    ("Meyerhans Mühlen AG", "5612", "Villmergen"),
    ("Meyerhans Mühlen AG", "6102", "Malters"),
    ("Meyerhans Mühlen AG", "8570", "Weinfelden"),
    ("Molino e Pastificio SA", "7742", "Poschiavo"),
    ("Moulin de la Pallanterie SA", "1222", "Vésenaz"),
    ("Moulin de la Vaux", "1170", "Aubonne"),
    ("Moulin de Romont SA", "1680", "Romont"),
    ("Moulin de Vicques Charmillot SA", "2824", "Vicques"),
    ("Moulins Chevalier SA", "1148", "Cuarnens"),
    ("Mühle Burgholz AG", "3753", "Oey-Diemtigen"),
    ("Mühle Fischer Lüscherz", "2576", "Lüscherz"),
    ("Mühle Fraubrunnen (Hans Messer + Co. AG)", "3312", "Fraubrunnen"),
    ("Mühle Kleeb AG", "3418", "Rüegsbach"),
    ("Obermühle Boswil AG", "5623", "Boswil"),
    ("Scartazzini u. Co.", "7606", "Promontogno"),
    ("Schweiz. Schälmühle E. Zwicky AG", "8554", "Müllheim-Wigoltingen"),
    ("Société Coopérative du Moulin de Payerne", "1530", "Payerne"),
    ("Stadtmühle Schenk AG", "3072", "Ostermundigen"),
    ("Strahm Mühle AG", "3110", "Münsingen"),
    ("Stricker & Cie AG (Handelsmühle)", "9472", "Grabs"),
    ("Swissmill", "8050", "Zürich"),
    ("Wicki Mühle AG", "6170", "Schüpfheim"),
    ("Willi Grüninger AG", "8890", "Flums"),
]

SEARCH = "https://api3.geo.admin.ch/rest/services/api/SearchServer"


def _query(text):
    q = {"searchText": text, "type": "locations",
         "origins": "zipcode,gg25,address", "sr": "4326", "limit": "1"}
    req = Request(f"{SEARCH}?{urlencode(q)}", headers={"User-Agent": "sfr-mills-etl/1.0"})
    with urlopen(req, timeout=30) as r:
        res = json.loads(r.read().decode("utf-8")).get("results", [])
    if not res:
        return None
    a = res[0]["attrs"]
    return (a.get("lon"), a.get("lat"))


def geocode(name, plz, ort):
    for text in (f"{plz} {ort}", ort, plz, f"{ort} {name.split('(')[0]}"):
        try:
            xy = _query(text)
        except Exception:
            xy = None
        time.sleep(0.15)
        if xy and xy[0] is not None and xy[1] is not None:
            return xy, text
    return None, None


def main():
    feats, misses = [], []
    for name, plz, ort in MILLS:
        (xy, used) = geocode(name, plz, ort)
        if not xy:
            misses.append(f"{name} ({plz} {ort})")
            print(f"  ✗ {name} ({plz} {ort})", file=sys.stderr)
            continue
        feats.append({"type": "Feature",
                      "properties": {"name": name, "ort": ort, "plz": plz},
                      "geometry": {"type": "Point", "coordinates": [round(xy[0], 6), round(xy[1], 6)]}})
        print(f"  ✓ {name} → {ort} [{used}]", file=sys.stderr)

    fc = {"type": "FeatureCollection",
          "properties": {"source": "DSM member directory (dsm-fms.ch), geocoded via geo.admin.ch",
                         "note": "DSM members ≈ >96% of Swiss soft-wheat milling"},
          "features": feats}
    with open("mills.geojson", "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False)
    print(f"\nWrote mills.geojson: {len(feats)}/{len(MILLS)} geocoded"
          + (f", {len(misses)} missing" if misses else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
