# Changelog

Alle bemerkenswerten Änderungen an diesem Plugin werden hier dokumentiert.

Format angelehnt an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [4.0.1] — 2026-04-23

### Fixed

- Defekte Template-Pfade in drei Skills. `advisor`, `methodology-advisor` und `submission-checker` verwiesen auf `${CLAUDE_PLUGIN_ROOT}/templates/...`, die referenzierten Dateien liegen jedoch skill-lokal. Die Skills brachen zur Laufzeit bei Exposé-Generierung, Methodenkatalog-Lookup und FH-Requirements-Check (#12, #13, #14).
- Offene Agent-Permissions in `commands/search.md`. `allowed-tools: Agent` ließ Aufruf beliebiger Subagenten zu — Privilege-Eskalations-Risiko. Jetzt eingeschränkt auf `Agent(query-generator, relevance-scorer, quote-extractor)` (#15).
- Agent-Frontmatter normalisiert. Alle drei Agenten hatten `tools: ""` (mehrdeutiger Leerstring) und einzeilige Descriptions ohne `<example>`-Blöcke. `tools`-Feld entfernt bzw. als Array gesetzt, Descriptions um je zwei `<example>`-Blöcke ergänzt (#16, #17).

### Changed

- `quote-extractor.maxTurns` von 20 auf 5 reduziert. Extraktion ist near-single-shot; 20 war Overkill (#18).
- `relevance-scorer.maxTurns` von 15 auf 3 reduziert. Ein Batch von 10 Papern = 1 Turn, 2 Puffer für Iteration (#18).

## [4.0.0] — Vor 2026-04-23

Erstes getracktes Release. Siehe Git-Historie für frühere Änderungen.
