# Swiss Farm/Parcel Suitability Map — Build Plan

**Purpose:** A zero-learning-curve web map that lets research colleagues build dynamic heatmaps of parcels most likely to fit a given agronomic profile (e.g. mixed-crop adoption) *before* going into the field with questionnaires. Built entirely on public Swiss geodata. General-purpose from day one. Static snapshot for v1.

**Scope decisions (confirmed):** v1 covers only cantons whose parcel data is openly accessible (no data-agreement chase); public-data proxies for protected attributes are accepted as research-valid.

**Core reframe (agreed):** The tool highlights *parcels/areas*, not named individuals. Colleagues identify the actual farmer on the ground or via the canton. This is not a limitation to work around — it is the only legally clean design on public data, and it fits the mixed-crop use case almost perfectly (that question is driven by land use + soil + terrain, which *are* public).

---

## 1. The honest data-availability picture

The single most important design fact: **what is public in Switzerland splits sharply between "the land" and "the farmer."**

| Layer | Public & national? | Access | Resolution |
|---|---|---|---|
| Current crop / land use per parcel (Nutzungsflächen, LBV codes) | Yes, national | geodienste.ch — **access set per canton; several require authorization/fees** | Parcel |
| Slope / Hangneigung | Yes | geo.admin.ch (free) | 10 m raster |
| Elevation (swissALTI3D / DHM) | Yes | geo.admin.ch / swisstopo (free) | 0.5–10 m |
| Soil suitability (Bodeneignungskarte BLW) | Yes | geo.admin.ch / opendata.swiss (free) | ~raster/polygon |
| Land-use & land-cover statistics (Arealstatistik BFS) | Yes | geo.admin.ch / opendata.swiss (free) | 100 m hectare grid |
| Climate (temperature, precipitation, growing season) | Yes | MeteoSwiss / opendata.swiss (free) | grid/station |
| **Farm counts, LN, livestock, Betriebsform, Betriebssystem (organic/conv.)** | **Yes, national** | **BFS STAT-TAB PxWeb API (free, no auth)** | **Canton × production zone × year** |
| **Farm type / Betriebsform per parcel** (Bewirtschaftungseinheit) | Data exists | **"verwaltungsintern" — NOT public** | Parcel→farm |
| **Farm size, livestock counts, organic status per individual farm** | Exists in AGIS/Agate | **Not public** | Farm |
| **Individual direct payments** | Exists at BLW | **Not public** (federal transparency initiative was blocked) | Farm |
| **IP-Suisse membership** | — | Not open geodata | Farm |

**Consequence for your filter list:**

- **Fully backed by public data, per parcel:** current crop mix, slope, elevation, soil suitability, climate/growing conditions.
- **Backed by public data, but only aggregated (canton × production zone):** Betriebsform (farm type), organic vs conventional (Betriebssystem), livestock — via the BFS STAT-TAB table you flagged. These become regional overlays/denominators, not parcel filters.
- **Not available anywhere public:** per-individual-farm size, IP-Suisse membership, direct-payment category. Fieldwork columns only.

We do NOT fake these. Each attribute gets the strongest treatment its real data resolution allows (below).

---

## 2. How each requested filter is handled

**Direct (real public data):**

- **Current crop mix** → Nutzungsflächen LBV land-use codes per parcel. This is the backbone.
- **Slope** → `ch.swisstopo.hangneigung` / derived from swissALTI3D; thresholds adjustable (e.g. exclude > 18 % for arable).
- **Elevation** → swissALTI3D / DHM; e.g. cap at the arable-cropping altitude ceiling.
- **Soil suitability** → BLW Bodeneignungskarte sub-layers: cultivated land (Kulturland), crop type (Kulturtyp), waterlogging (Vernässung), stone content (Skelettgehalt), permeability, rooting depth.
- **Climate / growing season** → MeteoSwiss temperature sum, precipitation, growing-season length.

**Regional statistical overlay (BFS STAT-TAB — real public data, aggregated to canton × production zone):**

- **Betriebsform (farm type)** → share/count of each farm type per canton and production zone (classification level 3). Lets colleagues weight or shade regions by, e.g., prevalence of arable/mixed farms.
- **Organic vs conventional (Betriebssystem)** → organic-farm share per canton/zone.
- **Livestock** → livestock numbers/farm counts per canton/zone (table `_108`), as a regional cross-check on the parcel-level livestock proxy.

These are true numbers, just not parcel-resolved — ideal as choropleth context and as sampling denominators for the fieldwork design.

**Parcel proxy (public land-use data stands in for a protected attribute — clearly labelled as an estimate):**

- **Livestock presence, per parcel** → derived from land use: high share of permanent/temporary grassland, silage/fodder, alpine pasture ⇒ likely animal-based. This is exactly your "exclude all animal-based systems" step, cross-checkable against the BFS regional livestock overlay.
- **Farm size** → *cannot* be reconstructed per farm from public data (needs the internal Bewirtschaftungseinheit link). Optional weak proxy: mean contiguous parcel size in an area. Flag as low-confidence.

**Fieldwork columns (not modellable at all from public data — captured after contact):**

- **Per-farm size, IP-Suisse, direct-payment category** → filled by the research team; carried through export so field results enrich the dataset over time.

Key expectation to lock in: the mixed-crop question is fully answerable at parcel level; Betriebsform/organic/livestock inform *where to look* via regional statistics; per-farm specifics are fieldwork outputs.

---

## 3. Worked example — "which parcels are most likely to adopt mixed crop systems?"

This is the reference query the model is built to serve, expressed as tweakable rules:

1. **Exclude animal-based systems** → drop parcels whose current land use is grassland/fodder/pasture-dominated (livestock proxy).
2. **Exclude where mixed crops can't grow** → require soil suitability = cultivated-crop-capable AND slope below threshold AND elevation below threshold AND adequate growing-season/climate.
3. **Other factors (weightable):** already-diverse current crop rotation nearby, proximity to existing arable parcels, water availability/permeability, low stone content.

Output = a heatmap where each surviving parcel gets a 0–100 "adoption-suitability" score from the weighted factors, so colleagues eyeball hotspots and pick field sites. Every threshold and weight is exposed in the UI.

---

## 4. Architecture (v1 = static snapshot)

Because v1 is static and needs zero learning curve, the pragmatic design is **pre-processed snapshot → lightweight web map**, not live queries against a dozen WFS endpoints (which would be slow and fragile given per-canton access rules).

```
[ Public sources ]                [ Build step (periodic) ]        [ Delivered artifact ]
 geodienste WFS/WMS   ─┐
 geo.admin soil/slope ─┤  ETL: fetch → clip to CH → harmonize →   Static web map
 swissALTI3D          ─┼─ compute per-parcel attributes →         (MapLibre GL + vector
 Arealstatistik BFS   ─┤  score → export vector tiles / GeoJSON   tiles), client-side
 MeteoSwiss climate   ─┘  + attribute table                       filtering & scoring
```

- **Build/ETL:** Python (GeoPandas, rasterio, owslib) run on a schedule (quarterly, matching data cadence). Produces one harmonized parcel table with all public attributes attached (spatial join of parcels × soil/slope/elevation/climate).
- **Storage:** vector tiles (parcels) + a compact attribute file; terrain/soil as raster tiles or pre-sampled per parcel.
- **Frontend:** a single self-contained web map (MapLibre GL JS, free/open, uses swisstopo basemaps). Filters and the suitability score run **client-side** so sliders update the heatmap instantly with no backend.
- **Tweakability:** a control panel of sliders/toggles (thresholds + factor weights) → recolours the heatmap live. Presets ("Mixed-crop adoption", "Blank") so the default view needs zero setup.
- **Export:** selected parcels → CSV/GeoJSON (coordinates + attributes) for field routing.

Later (v2+) some layers can go live via WMS/WFS if colleagues want always-fresh data; the static core stays as the fast path.

---

## 5. Data source reference (endpoints)

- **Parcel land use (crop mix):** geodienste.ch *Landwirtschaftliche Bewirtschaftung: Nutzungsflächen* — WFS/OGC API Features, INTERLIS model LWB_Nutzungsflaechen v2.0/v3.0. National, structurally harmonized across cantons; **verify per-canton access tier during build.**
- **Soil suitability:** BLW *Digitale Bodeneignungskarte der Schweiz* — layers `ch.blw.bodeneignung-kulturland`, `-kulturtyp`, `-vernaessung`, `-skelettgehalt`, permeability, rooting depth (geo.admin.ch WMS/WMTS/REST; opendata.swiss).
- **Slope:** `ch.swisstopo.hangneigung*` (derived from swissALTI3D, 10 m).
- **Elevation:** swissALTI3D / DHM (swisstopo, geo.admin.ch).
- **Land-use/-cover statistics:** BFS Arealstatistik `ch.bfs.arealstatistik` (NOAS04/NOLC04), hectare grid.
- **Climate:** MeteoSwiss climate normals / gridded products via opendata.swiss.
- **Farm structure statistics (regional overlays):** BFS STAT-TAB PxWeb API — tables `px-x-0702000000_106` (farms + LN by canton × production zone × Betriebssystem × Betriebsform × year) and `px-x-0702000000_108` (farms + livestock, same breakdown). Base `https://www.pxweb.bfs.admin.ch/api/v1/de/`; free, no auth; JSON-stat2; 5000 values/call. Grab the exact query JSON from each table's "API Query for" panel.
- **API base:** geo.admin.ch REST — `https://api3.geo.admin.ch/services/sdiservices.html`; tiles `https://wmts.geo.admin.ch/`; projection EPSG:2056 (LV95).

---

## 6. Phased roadmap

- **Phase 0 — Data feasibility spike (fast):** confirm per-canton access tier for Nutzungsflächen (which cantons are open vs authorization-required), pull one canton end-to-end, validate the LBV crop codes and the grassland/livestock proxy. Decide whether nationwide parcel coverage is achievable on open access alone or needs a data agreement for some cantons.
- **Phase 1 — Terrain + soil + climate map (no parcels):** ship a working national heatmap on the fully-open layers (slope, elevation, soil suitability, climate) with tweakable thresholds. Already useful; de-risks the frontend.
- **Phase 2 — Add parcel land use + mixed-crop model + BFS overlays:** join crop-use parcels, implement the 3-step example as adjustable rules + 0–100 score, add the BFS STAT-TAB regional overlays (Betriebsform / organic / livestock as canton-zone choropleths), presets and export.
- **Phase 3 — General-purpose polish:** save/share filter presets, additional example queries, documentation.
- **Phase 4 (optional) — Live mode & fieldwork loop:** live WFS refresh; let colleagues push field-collected attributes (organic, farm size, willingness) back as a layer.

---

## 7. Locked parameters

All build parameters are now fixed:

- **Coverage:** open-access cantons only for v1; excluded cantons shown greyed-out with an explanatory note.
- **Attributes:** public-data proxies accepted (livestock-from-land-use, etc.).
- **Refresh:** annual snapshot (matches source cadence for both land-use and BFS structure data).
- **Hosting:** simple static hosting — a single self-contained bundle (HTML/JS + vector tiles + attribute file), no server-side runtime.
- **Language:** German (DE).

Nothing else blocks the build.

---

*Note on sources: individual-farm attributes are not available as public geodata at parcel resolution. Betriebsform, organic status and livestock ARE public but only aggregated to canton × production zone (BFS STAT-TAB) — used as regional overlays. Per-farm size, IP-Suisse and direct-payment category remain fieldwork-only. All other layers are public federal/cantonal geoservices.*
