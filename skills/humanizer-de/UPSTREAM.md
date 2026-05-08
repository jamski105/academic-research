# Upstream-Provenienz: humanizer-de

| Feld | Wert |
|------|------|
| Repository | https://github.com/marmbiz/humanizer-de |
| upstream commit SHA | `d3b4a8d0590ec7c1d5c17213909450392dedf079` |
| Clone-Datum | 2026-05-08 |
| Vendor-Version | `3.2.4-de.1-vendored` |
| Ursprünglicher Autor | Martin Moeller (www.martin-moeller.biz) |
| Lizenz | MIT |

## Anpassungen gegenüber Upstream

1. **Frontmatter** — auf academic-research-Konventionen umgestellt
   (`allowed-tools` statt `allowed_tools`, `name: humanizer-de` lowercase,
   `upstream_sha`-Feld ergänzt).

2. **Split-Design** — upstream SKILL.md (1040 LOC) aufgeteilt in:
   - `SKILL.md` (~170 LOC): Laufzeit-Anweisungen
   - `references/patterns.md` (~850 LOC): Musterbibliothek (analog zu
     `skills/citation-extraction/` Referenzstruktur)

3. **Modus-Erweiterung** — `deep`-Modus dokumentiert
   (upstream hat locker/Sachlich/formal; `deep` = Sachlich + zweiter Anti-KI-Pass).

4. **Severity-Mapping** — neue Tabelle für Diff-Output-Integration mit
   `/academic-research:humanize` Command (nicht in upstream vorhanden).

5. **Voice-Calibration-Parameter** — `voice_samples_dir` als Skill-Parameter
   statt inline Dateiübergabe.

6. **Attribution** — HTML-Kommentar und Frontmatter-Felder ergänzt.
