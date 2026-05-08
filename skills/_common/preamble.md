# Gemeinsames Preamble — academic-research Skills

Dieses Preamble gilt für alle Skills dieses Plugins.
Jeder Skill lädt diese Datei am Anfang seiner Aktivierung.

## Vorbedingungen

Bevor du startest: Prüfe, ob `./academic_context.md` und `./literature_state.md`
vorhanden und aktuell sind. Fehlt Kontext → triggere den `academic-context`-
Skill und warte auf dessen Abschluss.

Lehnt der User den Trigger ab → brich diesen Skill ab und erkläre:
"Ohne Forschungsfrage und Methodik-Angabe kann ich kein belastbares Ergebnis
liefern, weil ich ein erfundenes Thema beschreiben würde."

## Keine Fabrikation

Erfundene Ergebnisse, Methoden oder Zahlen sind ein Täuschungsversuch nach
FH-Leibniz-Prüfungsordnung und führen zum Verlust der Prüfungsleistung.
Arbeite ausschließlich mit Inhalten aus `./writing_state.md` (Arbeitstext)
und `./academic_context.md` (Forschungsfrage, Methodik). Fehlen Daten: frag
den User, rate nicht.

## Aktivierung

- Der User aktiviert einen Skill dieses Plugins explizit oder durch Trigger-Phrase
- Der User-Auftrag passt zur Skill-Beschreibung im Frontmatter

## Abgrenzung

Jeder Skill definiert in seiner eigenen `## Abgrenzung`-Section, was er liefert
und was er nicht liefert. Fehlt diese Section im Skill, gilt: Skill nur für den
im Frontmatter beschriebenen Zweck einsetzen.

---

## Hinweise für Skill-Maintainer

### Variant-Referenzen

Variant-Referenzen (z.B. citation-extraction/references/) erst nach
Variant-Fixierung laden (lazy per Read-Anweisung im Skill).

### Browser-Snapshots

Raw-DOM-Ausgaben des `browser-use`-CLI in `$SESSION_DIR/raw/` speichern.
Dem Modell nur das normalisierte Schema-Result zurückgeben
(`title`, `authors`, `year`, `url`, `abstract`).
