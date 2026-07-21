# Parzellen-Eignungskarte Schweiz — Anleitung

Eine statische Web-Karte, die landwirtschaftliche Parzellen der ganzen Schweiz
nach Eignung für die Mischkultur-Adoption einfärbt (0–100), plus regionalen
BFS-Kontext (Bio-Anteil, Betriebsform, Grünland) pro Kanton. Basiert
ausschliesslich auf öffentlichen Geodaten (geodienste.ch, geo.admin.ch, BFS).

Für die Forschung: dynamische Karten erstellen, *bevor* man mit Fragebögen ins
Feld geht.

---

## Dateien in diesem Ordner

| Datei | Zweck | Für wen |
|---|---|---|
| `parzellen-eignungskarte.html` | Die Karte. Das ist alles, was Betrachter brauchen. | alle |
| `build_canton.py` | Optional: bäckt einen Kanton in eine statische Datei (mit Boden/Hangneigung). | techn. Person |
| `build_bfs.py` | Optional: lädt die BFS-Kantonszahlen als Datei. | techn. Person |
| `farm-parcel-map-build-plan.md` | Konzept & Architektur. | Doku |
| `phase0-spike-findings.md` | Datenverfügbarkeit & Machbarkeit. | Doku |

Kolleg:innen, die nur schauen wollen, brauchen **nur die URL** der gehosteten
Karte — die Python-Skripte fassen sie nie an.

> **Wichtig:** Die Karte per Doppelklick zu öffnen (`file://`) funktioniert nur
> eingeschränkt — der Browser blockiert das Nachladen der Daten. Die Karte muss
> **über HTTP ausgeliefert** (gehostet) werden. Deshalb diese Anleitung.

---

## Variante A — GitHub Pages (kostenlos, empfohlen)

Ergebnis: eine Link-URL, die alle im Browser öffnen können.

1. Konto auf <https://github.com> erstellen (falls noch keins).
2. **New repository** → Name z.B. `parzellen-eignungskarte` → **Public** →
   *Create repository*.
3. **Add file → Upload files** → diese Dateien hochladen:
   - `parzellen-eignungskarte.html` (zwingend)
   - falls vorhanden: `parcels_scored.geojson`, `bfs_cantons.json`,
     `cantons.geojson` (die gebackenen Daten — optional, siehe unten)
   - *Commit changes*.
4. **Settings → Pages** → unter *Branch* `main` und `/ (root)` wählen → *Save*.
5. Nach ~1 Minute erscheint oben die Adresse, z.B.
   `https://<benutzername>.github.io/parzellen-eignungskarte/`
6. Die Karte liegt dann unter:
   `https://<benutzername>.github.io/parzellen-eignungskarte/parzellen-eignungskarte.html`
   → **dieser Link ist das, was du teilst.**

Aktualisieren: einfach die Datei(en) im Repo neu hochladen (Upload überschreibt).

Tipp: Wer die Startseite hübscher will, benennt die Karte in `index.html` um —
dann reicht die kurze URL `https://<benutzername>.github.io/parzellen-eignungskarte/`.

---

## Variante B — Institutioneller Webspace / SharePoint

- **Eigener Webserver / Intranet-Webspace:** die `.html` (und optionale
  Datendateien) in einen per HTTP ausgelieferten Ordner legen. Fertig.
- **SharePoint/OneDrive:** eignet sich schlecht — Dateien werden meist zum
  Download angeboten statt als Website dargestellt. Lieber Variante A oder den
  IT-Webspace nutzen.
- **Netlify Drop** (<https://app.netlify.com/drop>): Ordner ins Browserfenster
  ziehen → sofort eine öffentliche URL. Am schnellsten ohne Konto-Setup.

---

## Was die Karte ohne gebackene Daten kann

Die gehostete `.html` funktioniert **sofort** (Live-Modus): sie lädt Parzellen
beim Hineinzoomen direkt von geodienste.ch und die BFS-/Kantonsdaten live. Es
ist **keine** Ausführung der Python-Skripte nötig, um zu starten.

Die gebackenen Dateien (unten) machen die Karte schneller, offline-robuster und
unabhängig von möglichen CORS-Einschränkungen — empfohlen für den produktiven
Einsatz.

---

## Optional: Daten «backen» (technische Person, einmalig pro Kanton)

Voraussetzung: Python 3 auf dem eigenen Rechner (dort ist der Netzzugriff frei).

```bash
# BFS-Kantonszahlen (einmal für die ganze Schweiz)
python3 build_bfs.py                       # → bfs_cantons.json

# ein Kanton, Kultur-Score (schnell, ohne Zusatz-Downloads)
python3 build_canton.py --canton AG        # → parcels_scored.geojson

# optional mit Boden + Hangneigung/Höhe (braucht geopandas, rasterio, rasterstats)
python3 build_canton.py --canton AG \
    --soil bodeneignung_kulturland.gpkg --dem swissalti3d_ag.tif
```

Die erzeugten `.geojson`/`.json` einfach **neben** die `.html` legen (bzw. mit
ins Repo hochladen) — die Karte findet sie automatisch.

Zugriff pro Kanton: 24 von 26 Kantonen sind frei. **Tessin (TI)** verlangt
Registrierung, **Neuchâtel (NE)** nur für den Massen-Download.

---

## Hinweise

- Internet ist immer nötig (Kartenkacheln von swisstopo, Live-Daten).
- Sprache der Oberfläche: Deutsch.
- Der Eignungs-Score ist eine transparente Heuristik zur Priorisierung von
  Feldstandorten — keine validierte agronomische Bewertung; im Feld prüfen.
- Quellen: geodienste.ch (Nutzungsflächen), geo.admin.ch/BLW (Bodeneignung,
  Hangneigung), BFS STAT-TAB (Betriebsstruktur).
