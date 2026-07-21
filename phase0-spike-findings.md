# Phase 0 Data Spike — Findings

**Verdict: GO.** Every core data dependency resolved against live public endpoints. The "open-access cantons only" constraint costs almost nothing, and the parcel data carries named crop types at high density. Below is what was actually pulled and what it means for the build.

---

## 1. Canton access — near-complete national coverage

Pulled the live per-canton access table (`geodienste.ch/info/services.csv?base_topics=lwb_nutzungsflaechen`). Result for the Nutzungsflächen (parcel crop-use) layer:

- **~24 of 26 cantons: "Frei erhältlich"** (freely available) for both data download and WMS — no contract, free use, source attribution required.
- **Ticino (TI):** registration required for both data and WMS.
- **Neuchâtel (NE):** registration required for bulk *data download*; WMS is free.

So v1 (open-access only) effectively covers the whole country minus TI, with NE available via WMS. This is a much smaller compromise than feared — "all of Switzerland" is essentially achievable.

## 2. Parcel crop data — validated, dense, named

Pulled live parcels from the national OGC API Features endpoint (`.../lwb_nutzungsflaechen_v2_0_0/deu/ogcapi`). A 5×2 km test box returned **2,535 parcels**. Each parcel carries the fields the model needs:

| Field | Example | Use |
|---|---|---|
| `lnf_code` | `502` | Machine crop code (LBV/LN nomenclature) |
| `nutzung` | `Wintergerste` (winter barley) | Human-readable crop → drives crop-mix filter & livestock proxy |
| `flaeche_m2` | `6333` | Parcel area |
| `kanton` | `SO` | Canton filter |
| `bezugsjahr` | `2025` | Reference year (annual) |
| `beitragsberechtigt` | `true` | Direct-payment eligible |
| `ist_ueberlagernd` | `false` | Overlap flag (biodiversity layers overlay — must dedupe) |
| geometry | polygon (EPSG:2056) | The parcel shape for the map |

Three collections exist: `nutzungsflaechen` (full, the one we use), `nutzungsflaechen_hauptkategorien` (main categories), `nutzungsflaechen_bff_q1` (biodiversity areas).

**Implication:** the mixed-crop example is fully executable. "Exclude animal-based systems" = filter out grassland/fodder `nutzung` values (Kunstwiesen, Weiden, Dauerwiesen, Silo-/Grünmais); "where mixed crops can grow" = keep arable parcels and cross with soil/slope. The livestock proxy is real and code-driven, not hand-waved.

## 3. BFS regional overlay — richer than expected

Pulled live metadata for STAT-TAB table `px-x-0702000000_106`. Dimensions available (free API, JSON, annual 1975→2025):

- **Beobachtungseinheit:** farm counts **plus 66 crop-area categories in ha** (e.g. Kunstwiesen, Weiden, Silo-/Grünmais, Weizen, Gerste, Kartoffeln, Reben…). This alone gives a canton-level crop-structure profile.
- **Kanton:** all 26 + Switzerland.
- **Landwirtschaftliche Produktionszone:** Talzone, Hügelzone, Bergzone 1–4 — matches how agronomists think about growing conditions.
- **Betriebssystem: Biologische vs Konventionelle Betriebe** → the organic-share overlay, confirmed available.
- **Betriebsform (in this table): Haupt- vs Nebenberuflich** (full-/part-time).

**Nuance to resolve in build:** the arable/dairy/mixed *farm typology* (the "Betriebstyp" sense of Betriebsform you originally meant) is a distinct classification — likely in a sibling STAT-TAB table (`_108` or related). The organic overlay and crop-structure profile are already confirmed here; the farm-typology table will be pinned down in Phase 2. No blocker.

---

## 4. Confirmed data stack for the build

| Purpose | Source | Status |
|---|---|---|
| Parcel crop use | geodienste OGC API Features `nutzungsflaechen` | ✅ live, named crops |
| Canton access map | geodienste services.csv | ✅ 24/26 open |
| Soil suitability | geo.admin `ch.blw.bodeneignung-*` | ✅ (documented, standard WMS/WMTS) |
| Slope | geo.admin `ch.swisstopo.hangneigung` | ✅ |
| Elevation | swissALTI3D / DHM | ✅ |
| Organic + crop structure by canton/zone | BFS STAT-TAB `_106` | ✅ live metadata verified |

## 5. Recommended next actions (Phase 1 → 2)

1. **Phase 1 build:** static MapLibre shell + terrain/soil/slope layers + tweakable sliders and the mixed-crop preset — no parcel ETL yet. Fastest path to a clickable tool.
2. **Phase 2 build:** wire the parcel ETL (start with one open canton, e.g. Aargau or Solothurn), dedupe overlapping features via `ist_ueberlagernd`, implement the 0–100 adoption score, add the BFS organic/crop-structure overlay, and pin down the farm-typology table.
3. **Housekeeping:** cache the annual snapshot; store the parcel layer as vector tiles keyed by `lnf_code`; expose crop-group and grassland/livestock toggles from the `nutzung` field.

*All endpoints above were queried live during this spike (July 2026) and returned valid data.*
