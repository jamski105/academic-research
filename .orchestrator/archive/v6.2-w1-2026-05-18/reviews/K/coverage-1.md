# Coverage Report — Chunk K (cluster-visualizer) — PR #132 — Iteration 1

**Ticket:** #79 — v6.2 · F11 — Cluster-Visualisierung als Mermaid-Diagramm
**PR:** #132 — v6.2: Cluster-Visualisierung als Mermaid-Diagramm
**Date:** 2026-05-18

---

## ACs aus Issue #79 / Ticket 79.draft.md

### AC1: Skill `cluster-visualizer` nimmt ein Cluster-JSON als Input und produziert validen Mermaid-`graph LR`-Quelltext

**PASS**

- Implementiert: `skills/cluster-visualizer/scripts/render_mermaid.py` — Funktion `cluster_to_mermaid()` (diff Zeile 199–225) erzeugt explizit `["graph LR"]` als ersten Eintrag der `lines`-Liste.
- Getestet: `tests/test_cluster_visualizer.py::test_mermaid_graph_header` (diff Zeile 1162–1165) assertiert `src.startswith("graph LR")`.

---

### AC2: Knoten repräsentieren Paper (Titel + Jahr als Label)

**PASS**

- Implementiert: `render_mermaid.py` — `_sanitize_label(title, year)` (Zeile 152–163) gibt `f"{safe_title} {year}"` zurück; in `cluster_to_mermaid()` wird das Label als `{node_id}["{label}"]` eingefügt.
- Getestet: `test_all_eight_nodes_present` (Zeile 1168–1172) prüft alle 8 Paper-IDs im Output. Der 8-Paper-Fixture enthält Titel + Jahr je Paper, sodass der Test die Label-Logik implizit abdeckt. Zusätzlich prüft `test_label_sanitization` die Label-Syntax direkt (Zeile 1236–1261).

---

### AC3: Kanten repräsentieren geteilte Zitate (Kantengewicht via Strichdicke, `linkStyle`)

**PASS**

- Implementiert: `render_mermaid.py` — `cluster_to_mermaid()` generiert `{from_id} -->|"{w}"| {to_id}` und `linkStyle {link_index} stroke-width:{sw}px` mit `_stroke_width(weight)` (Zeilen 213–223).
- Getestet:
  - `test_edge_weight_in_label` (Zeile 1179–1185): assertiert `'smith2021 -->|"3"| jones2020'` für weight=3.
  - `test_linkstyle_stroke_width_for_weight3` (Zeile 1191–1196): assertiert `"stroke-width:6px"` für weight=3 (weight*2=6).

---

### AC4: Skill aktiviert auf User-Phrasen „zeige Cluster", „visualisiere" und „Mindmap" (3 Trigger, per Eval verifiziert)

**PASS**

- Implementiert: `skills/cluster-visualizer/SKILL.md` (diff Zeile 7–18) enthält alle drei Phrasen explizit im `description`-Frontmatter: `"zeige Cluster"`, `"visualisiere"`, `"Mindmap"`.
- Getestet: `tests/test_cluster_visualizer.py::test_skill_trigger_phrases` (Zeile 1268–1274) iteriert über alle drei Trigger-Phrasen und assertiert deren Vorkommen in SKILL.md.

Hinweis: Die AC verlangt Verifikation „per Eval". Der Test ist ein statischer String-Match auf die SKILL.md — kein dynamisches Eval gegen ein LLM. Das entspricht dem in der Spec (K.md, Test-Anforderung 4) beschriebenen Ansatz und ist ausreichend.

---

### AC5: Skill gibt Mermaid-Quelltext aus und den Pfad zu einem gerenderten PNG (erzeugt via Mermaid-CLI `mmdc`)

**PASS**

- Implementiert: `render_cluster()` in `render_mermaid.py` (Zeilen 232–278) schreibt `.mmd`-Datei, ruft `mmdc` als subprocess list-form auf (`["mmdc", "-i", ..., "-o", ...]` Zeile 263–267, kein `shell=True`), und gibt `{"mermaid_source": ..., "mmd_path": ..., "png_path": ..., "note": ...}` zurück.
- Getestet: `test_graceful_degradation_no_mmdc` (Zeile 1203–1213) prüft den return-Wert inklusive `mmd_path` und `mermaid_source`. Da `mmdc` in der Test-Umgebung typischerweise nicht installiert ist, wird der Degradation-Pfad getestet. Es existiert kein Test der den Happy-Path mit echtem mmdc testet — dies ist per Spec akzeptiert (mmdc optional, Graceful Degradation als Hauptfall).

---

### AC6: Test-Cluster mit 8 Papern: Mermaid-Code ist syntaktisch valide (kein Parse-Fehler via `mmdc`) und das erzeugte PNG ist eine nicht-leere Bilddatei

**PARTIAL PASS — mit Einschränkung**

- Implementiert: `tests/fixtures/cluster_json/test_cluster_8.json` (diff Zeile 1094–1131) enthält exakt 8 Paper und 9 Edges.
- Getestet (Mermaid-Syntax): `test_mermaid_graph_header` + `test_all_eight_nodes_present` + `test_edge_weight_in_label` + `test_linkstyle_stroke_width_for_weight3` prüfen strukturelle Korrektheit des generierten Mermaid-Quelltexts.
- **Lücke — PNG-Validierung:** Die AC verlangt explizit, dass das erzeugte PNG eine nicht-leere Bilddatei ist. Es existiert kein Test in der PR-Diff, der (a) `mmdc` aufruft und (b) die Ausgabedatei auf Nicht-Leere prüft. Der Graceful-Degradation-Test mockt `shutil.which` auf `None` — er läuft bewusst ohne mmdc. Dies ist eine Abweichung von der wörtlichen AC. Begründung für Partial statt FAIL: die Extra-Anforderungen aus dem Prompt erlauben graceful degradation explizit als Primärpfad; die syntaktische Validität ist durch strukturelle Tests abgedeckt. Der PNG-Validierungstest fehlt dennoch.

---

### AC7: Skill folgt dem Plugin-Design-Prinzip: Agent/Skill-Implementierung, kein eigenständiges Python-Skript

**PASS**

- Implementiert: `skills/cluster-visualizer/SKILL.md` definiert den Skill als Agent-Skill mit Workflow-Dokumentation. `render_mermaid.py` liegt unter `skills/cluster-visualizer/scripts/` (nicht im Root) und ist als Helper konzipiert (analog zu `scripts/book_resolve.py`). Das Skript hat zwar einen `__main__`-Einstieg (CLI-Hilfe), ist aber primär als importierter Helper strukturiert.
- Getestet: `test_skill_trigger_phrases` prüft SKILL.md-Existenz und Inhalt — implizite Verifikation der Skill-Struktur.

---

## Extra-Anforderungen (aus Prompt)

### E1: SKILL.md vorhanden

**PASS** — `skills/cluster-visualizer/SKILL.md` neu in diff (Zeile 1–110).

### E2: `render_mermaid.py` als separater Helper

**PASS** — `skills/cluster-visualizer/scripts/render_mermaid.py` neu in diff (Zeile 113–292).

### E3: mmdc Graceful Degradation (Mermaid-Quelltext-Fallback bei fehlender CLI)

**PASS** — `shutil.which("mmdc") is None` → return ohne png, mit note (Zeile 253–259). Getestet: `test_graceful_degradation_no_mmdc`.

### E4: Output als separate Datei + Pfad-Return

**PASS** — `mmd_path.write_text(src)` + return `{"mmd_path": str(mmd_path), ...}` (Zeilen 250–251, 255–258).

### E5: subprocess list-form (kein `shell=True`)

**PASS** — `subprocess.run(["mmdc", "-i", str(mmd_path), "-o", str(png_path)], check=True, capture_output=True)` — kein `shell=True` (Zeile 263–267).

### E6: 8-Paper-Cluster-Fixture

**PASS** — `tests/fixtures/cluster_json/test_cluster_8.json` mit 8 Papern und 9 Edges (diff Zeile 1094–1131).

---

## Zusammenfassung

| AC | Status | Kritisch |
|---|---|---|
| AC1: graph LR Quelltext | PASS | nein |
| AC2: Knoten Titel+Jahr | PASS | nein |
| AC3: Kanten + linkStyle | PASS | nein |
| AC4: 3 Trigger-Phrasen | PASS | nein |
| AC5: Mermaid + PNG-Pfad-Return | PASS | nein |
| AC6: 8-Paper-Cluster + PNG nicht-leer | PARTIAL — PNG-Validierungstest fehlt | nein (mmdc optional per Spec) |
| AC7: Plugin-Design-Prinzip | PASS | nein |

**Kritische Lücken:** 0
**Hohe Lücken:** 0
**Anmerkung AC6:** Kein Test assertiert das erzeugte PNG als nicht-leere Bilddatei. Da die Spec und Prompt-Extras mmdc als optional definieren und Graceful Degradation als Primärpfad verlangen, ist dies kein kritischer Fehler — aber eine Lücke gegenüber dem wörtlichen AC.
