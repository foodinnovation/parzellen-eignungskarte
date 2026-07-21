# Parzellen-Eignungskarte Schweiz

Eine statische Web-Karte, die landwirtschaftliche Parzellen der ganzen Schweiz
nach Eignung für die Mischkultur-Adoption einfärbt (0–100), plus Getreidemühlen-
Standorten und regionalem BFS-Kontext (Bio-Anteil, Betriebsform, Grünland) pro
Kanton. Basiert ausschliesslich auf öffentlichen Geodaten (geodienste.ch,
geo.admin.ch/BLW, BFS, MeteoSchweiz/Open-Meteo, DSM).

Für die Forschung: dynamische Karten erstellen, *bevor* man mit Fragebögen ins
Feld geht. Die Karte hebt **Parzellen/Flächen** hervor, nie namentlich Personen —
das ist auf öffentlichen Daten die einzige rechtlich saubere Bauweise.

---

## 🔗 Die Karte live ansehen

**<https://foodinnovation.github.io/parzellen-eignungskarte/parzellen-eignungskarte.html>**

Das ist der Link zum Teilen. Kolleg:innen, die nur schauen wollen, brauchen
**nur diese URL** — die Python-Skripte fassen sie nie an. Nötig ist lediglich
eine Internetverbindung (Kartenkacheln von swisstopo, Live-Daten von
geodienste.ch).

> Die Karte wird über GitHub Pages aus diesem Repo ausgeliefert. Jeder Push auf
> den `main`-Branch aktualisiert die veröffentlichte Karte nach ~1 Minute
> automatisch.

---

## Was die Karte kann (ohne Zusatzdaten)

Die gehostete Karte funktioniert **sofort im Live-Modus** (ganze Schweiz): sie lädt
Parzellen beim Hineinzoomen (Stufe ≥ 13) direkt von geodienste.ch und die
BFS-/Kantonsdaten live. Es ist **keine** Ausführung der Python-Skripte nötig.

Der Score ist ein transparentes, gewichtetes Mittel aus bis zu **sechs** Faktoren –
**Kultur-Eignung, Bodeneignung, Terrain (Hang/Höhe), Umfeld-Diversität, Klima,
Mühlennähe** (Herkunft & Ableitung siehe [Score-Faktoren & Datenquellen](#score-faktoren--datenquellen)) –
alle Gewichte im Panel einstellbar. Kultur, Diversität, Klima und Mühlennähe sind
live überall verfügbar; **Boden und Terrain** holt die Karte auf **Klick** pro
Parzelle direkt von geo.admin (oder per Knopf «Sichtbare Parzellen anreichern»
für den ganzen Ausschnitt) — die Boden-/Terrain-Gewichte sind ausgegraut, solange
keine solchen Daten geladen sind. Ein Klick zeigt zudem **Luft- und Strassendistanz**
zur nächsten Getreidemühle (Strassenroute via OSRM).

Bedienung: Preset «Mischkultur-Eignung», Score-Gewichts-Regler, weiche
Hang-/Höhen-Schwellen, Kontext-Raster (Boden, Hangneigung) und ein
Kanton-Choropleth für den BFS-Kontext.

Die optional «gebackenen» Dateien (siehe unten) machen die Karte schneller,
offline-robuster und unabhängig von möglichen CORS-Einschränkungen — empfohlen
für den produktiven Einsatz.

---

## Score-Faktoren & Datenquellen

Der Eignungs-Score (0–100, türkise Skala) ist ein **gewichtetes Mittel** über die
pro Parzelle vorhandenen Faktoren. Alle Gewichte sind im Panel «Score-Gewichte»
einstellbar; jeder Faktor ist eine transparente Heuristik, keine validierte Bewertung.

| Faktor | Quelle | Wie abgeleitet | Verfügbar |
|---|---|---|---|
| **Kultur-Eignung** | geodienste.ch Nutzungsflächen (`nutzung`, `lnf_code`) | Feinklassierung: Leguminosen 95 · diverse Ackerkulturen 85 · Getreide 70 · Kunstwiese 55 · Dauerkultur 35 · Futterbau 20 · Grünland 5 (Vieh-Ausschluss) | immer (live) |
| **Bodeneignung** | BLW Bodeneignungskarte Kulturland (Stand 2008), via geo.admin `identify` am Parzellen-Zentroid | Text `eignungsei` → 0–100: Kulturart-Gewicht (Ackerbau 1.0 … Weide 0.15) × Eignungsnote (`++`=1.0, `+`=0.75, `+/-`=0.45); Siedlung/Fels/See → 5 | nach Anreicherung |
| **Terrain** | swisstopo `height`-API (swissALTI3D) | Höhe am Zentroid + Hangneigung aus Nachbarpunkten; weiche Straf­kurve rund um die eingestellten Hang-/Höhen-Schwellen | nach Anreicherung |
| **Umfeld-Diversität** | die geladenen Parzellen selbst | Shannon-Vielfalt der Kultur-Kategorien im ~500-m-Umkreis (Monokultur → 0, gemischt → ~100) | immer |
| **Klima** | MeteoSchweiz / Open-Meteo (ERA5) | Wachstumsgradtage (GDD, Basis 5 °C, Apr–Okt, Ø 2022/23), grobes Raster; GDD 900 → 0, 2000 → 100 | immer (`climate.json`) |
| **Mühlennähe** | DSM-Mühlenstandorte (`mills.geojson`) | Luftlinie zur nächsten Mühle → 100 an der Mühle, 0 bei der im Filter gewählten Radius-Distanz | immer · Standardgewicht 0 (aus) |

**«Nach Anreicherung»** = Boden/Terrain existieren erst, wenn du eine Parzelle
**anklickst**, «Sichtbare Parzellen anreichern» nutzt oder eine gebackene
`parcels_scored.geojson` lädst. Vorher sind diese beiden Regler ausgegraut
(«inaktiv, erst anreichern»).

### Getreidemühlen-Ebene
Ein-/ausblendbare Punkt-Ebene «Getreidemühlen (DSM)»: 36 Mitgliedsbetriebe des
**Dachverbands Schweizerischer Müller** (≈ >96 % der Weichweizenvermahlung ≈
praktisch alle gewerblichen Getreidemühlen), aus dem öffentlichen Mitglieder­verzeichnis
geocodiert (**PLZ-/ortsgenau**, nicht strassengenau). Zwei Verknüpfungen mit dem Score:
- **Filter** «Nur nahe einer Getreidemühle» + Radius-Regler (1–30 km) → blendet
  Parzellen jenseits des Radius aus.
- **Weicher Faktor** «Mühlennähe» (siehe Tabelle).

Beim Klick auf eine Parzelle zeigt das Popup **Luftlinie und Strassendistanz/-fahrzeit**
zur nächsten Mühle (Strassenroute via OSRM, on-demand pro Klick). Filter und Faktor
selbst rechnen bewusst mit Luftlinie (Routing für tausende Parzellen ist nicht praktikabel).

---

## Dateien in diesem Repo

| Datei | Zweck | Für wen |
|---|---|---|
| `parzellen-eignungskarte.html` | Die Karte. Das ist alles, was Betrachter brauchen. | alle |
| `cantons.geojson` | Kantonsgrenzen für die BFS-Choropleth (gebündelt). | — |
| `bfs_cantons.json` | BFS-Kantonskontext: Bio-Anteil, Haupterwerb, Grünland (gebündelt, Jahr 2025). | — |
| `climate.json` | Grobes Wachstumsgradtage-Raster (GDD) der Schweiz für den Klima-Faktor (gebündelt). | — |
| `mills.geojson` | Getreidemühlen-Standorte (DSM-Mitglieder, geocodiert) für die Mühlen-Ebene (gebündelt). | — |
| `build_canton.py` | Optional: bäckt einen Kanton in eine statische GeoJSON (mit Boden/Hangneigung). | techn. Person |
| `build_bfs.py` | Optional: erzeugt `bfs_cantons.json` neu (z.B. für ein anderes Jahr). | techn. Person |
| `build_climate.py` | Optional: erzeugt `climate.json` neu (Open-Meteo, GDD-Raster). | techn. Person |
| `build_mills.py` | Optional: erzeugt `mills.geojson` neu (DSM-Verzeichnis, geo.admin-Geocoding). | techn. Person |
| `farm-parcel-map-build-plan.md` | Konzept & Architektur, Roadmap. | Doku |
| `phase0-spike-findings.md` | Datenverfügbarkeit & Machbarkeit. | Doku |

`cantons.geojson`, `bfs_cantons.json` und `climate.json` sind **bewusst mitgeliefert**
(nationaler Kontext, klein), damit Choropleth und Klima-Faktor ohne externe Quellen
und ohne CORS-Probleme funktionieren. Die gehostete Karte ist ansonsten **live**:
Boden/Terrain kommen pro Klick bzw. per «Sichtbare Parzellen anreichern». Wer einen
ganzen Kanton vorbacken will, erzeugt mit `build_canton.py --geoadmin` eine
`parcels_scored.geojson` und legt sie neben die `.html` — die Karte lädt sie dann
automatisch (statt Live). Diese Datei wird nicht ins Repo eingecheckt.

> **Hinweis:** Die Karte per Doppelklick zu öffnen (`file://`) funktioniert nur
> eingeschränkt — der Browser blockiert das Nachladen der Daten. Die Karte muss
> **über HTTP ausgeliefert** werden. Genau das übernimmt GitHub Pages (oben).

---

## Aktualisieren

Änderungen an der Karte oder den Skripten committen und pushen — GitHub Pages
baut automatisch neu:

```bash
git add -A
git commit -m "…"
git push
```

Gebackene Datendateien mit ausliefern: entweder lokal neben die `.html` legen
(nur eigener Webserver), oder für GitHub Pages die entsprechende Zeile aus
`.gitignore` entfernen und die Datei mitcommitten.

---

## Optional: Daten «backen» (technische Person, einmalig pro Kanton)

Voraussetzung: Python 3 auf dem eigenen Rechner (dort ist der Netzzugriff frei).

```bash
# BFS-Kantonszahlen (einmal für die ganze Schweiz)
python3 build_bfs.py                       # → bfs_cantons.json

# Klima-Raster (Wachstumsgradtage, Open-Meteo, ganze Schweiz)
python3 build_climate.py                   # → climate.json

# Getreidemühlen (DSM-Mitgliederverzeichnis, via geo.admin geocodiert)
python3 build_mills.py                     # → mills.geojson

# ein Kanton, Kultur-Score (schnell, ohne Zusatz-Downloads)
python3 build_canton.py --canton AG        # → parcels_scored.geojson

# EMPFOHLEN: zusätzlich Boden + Hangneigung/Höhe pro Parzelle, direkt aus
# öffentlichen geo.admin-Diensten – kein Download, nur Standardbibliothek:
python3 build_canton.py --canton AG --geoadmin --max 1500

# (Alternative: aus lokalen Dateien; braucht geopandas, rasterio, rasterstats)
python3 build_canton.py --canton AG \
    --soil bodeneignung_kulturland.gpkg --dem swissalti3d_ag.tif
```

`--geoadmin` holt pro Parzelle die **Bodeneignung** (BLW `identify`) und
**Höhe + Hangneigung** (swisstopo `height`-API); die Werte fliessen als
Boden- und Terrain-Faktor in den Score ein (Gewichte im Panel). Aufrufe werden
auf einem 50-m-Raster zwischengespeichert; `--max` begrenzt die Parzellenzahl
beim Testen.

Zugriff pro Kanton: 24 von 26 Kantonen sind frei. **Tessin (TI)** verlangt
Registrierung, **Neuchâtel (NE)** nur für den Massen-Download.

---

## Alternative Hosting-Wege

- **Eigener Webserver / Intranet-Webspace:** die `.html` (und optionale
  Datendateien) in einen per HTTP ausgelieferten Ordner legen. Fertig.
- **SharePoint/OneDrive:** eignet sich schlecht — Dateien werden meist zum
  Download angeboten statt als Website dargestellt. Lieber GitHub Pages oder den
  IT-Webspace nutzen.
- **Netlify Drop** (<https://app.netlify.com/drop>): Ordner ins Browserfenster
  ziehen → sofort eine öffentliche URL. Am schnellsten ohne Konto-Setup.

---

## Hinweise

- Internet ist immer nötig (Kartenkacheln von swisstopo, Live-Daten).
- Sprache der Oberfläche: Deutsch.
- Der Eignungs-Score ist eine **transparente Heuristik** zur Priorisierung von
  Feldstandorten — keine validierte agronomische Bewertung; im Feld prüfen.
  Ackerkulturen erhalten hohe, Grünland/Futterbau (Viehhaltungs-Proxy) tiefe
  Werte; alle Schwellen und Gewichte sind im Panel einstellbar.
- Per-Betrieb-Merkmale (Betriebsgrösse, IP-Suisse, Direktzahlungen) sind **nicht**
  öffentlich und daher nicht in der Karte — sie bleiben Feldarbeit.
- Quellen: geodienste.ch (Nutzungsflächen), geo.admin.ch/BLW (Bodeneignung,
  Höhe/Hangneigung), BFS STAT-TAB (Betriebsstruktur), MeteoSchweiz/Open-Meteo
  (Klima/GDD), Dachverband Schweizerischer Müller DSM (Getreidemühlen),
  OSRM (Strassenrouting beim Klick). Alle öffentlich zugänglich.
- Die Getreidemühlen decken die DSM-Mitglieder ab (≈ >96 % der Vermahlung); sehr
  kleine, nicht-organisierte Mühlen können fehlen. Standorte sind orts-/PLZ-genau.
