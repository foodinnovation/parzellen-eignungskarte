# Parzellen-Eignungskarte Schweiz

Eine statische Web-Karte, die landwirtschaftliche Parzellen der ganzen Schweiz
nach Eignung für die Mischkultur-Adoption einfärbt (0–100), plus regionalen
BFS-Kontext (Bio-Anteil, Betriebsform, Grünland) pro Kanton. Basiert
ausschliesslich auf öffentlichen Geodaten (geodienste.ch, geo.admin.ch, BFS).

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

Die gehostete Karte funktioniert **sofort im Live-Modus**: sie lädt Parzellen
beim Hineinzoomen (Stufe ≥ 13) direkt von geodienste.ch und die BFS-/Kantons­daten
live. Es ist **keine** Ausführung der Python-Skripte nötig, um zu starten.

Bedienung: Filter-Panel mit Preset «Mischkultur-Eignung», Reglern für
Gewichtung (Boden, Hangneigung, Zonen) und Schwellen (max. Hangneigung, max.
Höhe), sowie einem Kanton-Choropleth für den BFS-Kontext.

Die optional «gebackenen» Dateien (siehe unten) machen die Karte schneller,
offline-robuster und unabhängig von möglichen CORS-Einschränkungen — empfohlen
für den produktiven Einsatz.

---

## Dateien in diesem Repo

| Datei | Zweck | Für wen |
|---|---|---|
| `parzellen-eignungskarte.html` | Die Karte. Das ist alles, was Betrachter brauchen. | alle |
| `cantons.geojson` | Kantonsgrenzen für die BFS-Choropleth (gebündelt). | — |
| `bfs_cantons.json` | BFS-Kantonskontext: Bio-Anteil, Haupterwerb, Grünland (gebündelt, Jahr 2025). | — |
| `parcels_scored.geojson` | Demo-Parzellen (AG, Seetal/Aare-Ebene, 500 Stück) mit Boden/Hang/Höhe – zeigt den angereicherten Score. | — |
| `build_canton.py` | Optional: bäckt einen Kanton in eine statische GeoJSON (mit Boden/Hangneigung). | techn. Person |
| `build_bfs.py` | Optional: erzeugt `bfs_cantons.json` neu (z.B. für ein anderes Jahr). | techn. Person |
| `farm-parcel-map-build-plan.md` | Konzept & Architektur, Roadmap. | Doku |
| `phase0-spike-findings.md` | Datenverfügbarkeit & Machbarkeit. | Doku |

`cantons.geojson`, `bfs_cantons.json` und die Demo-`parcels_scored.geojson` sind
**bewusst mitgeliefert**, damit Choropleth und angereicherter Parzellen-Score ohne
externe Quellen und ohne CORS-Probleme funktionieren. `parcels_scored.geojson`
lässt sich pro Kanton mit `build_canton.py --geoadmin` neu erzeugen; die Karte
findet sie automatisch, wenn sie neben der `.html` liegt (sonst Live-Modus).

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
  Hangneigung), BFS STAT-TAB (Betriebsstruktur).
