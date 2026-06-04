# Humanizer-Audit-Pass (nur Hochschul-Kontext)

Bevor `quality-reviewer` aufgerufen wird, prüft `SKILL.md`, ob ein
Anti-KI-Audit-Pass erforderlich ist.

## Trigger-Bedingung

1. Lies `./academic_context.md` (bereits in Schritt 1 geladen).
2. Extrahiere das Feld `Typ:` (Freitext, z. B. `Bachelorarbeit`).
3. Prüfe Substring-Match (case-insensitiv) gegen:
   `["bachelor", "master", "diplom", "dissertation"]`
4. Prüfe ob `humanizer_de: off` in `./academic_context.md` gesetzt ist.

**Humanizer überspringen wenn:**
- `./academic_context.md` fehlt, oder `Typ:` nicht gesetzt, oder kein
  Hochschul-Marker gefunden, **oder**
- `humanizer_de: off` in `./academic_context.md` gesetzt ist.

**Humanizer ausführen wenn:** Hochschul-Marker gefunden UND kein Bypass-Flag.

## Ausführung

```
Skill(humanizer-de):
  mode: formal
  input: <aktueller Kapitel-Entwurf>
  voice_samples_dir: <aus academic_context.md project_slug oder null>
```

Der Skill gibt zurück:
- `humanized_text` — überarbeiteter Entwurf (ersetzt den rohen Draft)
- `changes` — Liste der Änderungen mit `severity` und `pattern_id`

**Nach dem Audit-Pass:** Verwende `humanized_text` als Input für den
nachfolgenden `quality-reviewer`-Aufruf.

**Anzahl Critical/High-Änderungen** kurz dem User melden (z. B.:
`Humanizer-Audit: 3 Critical, 7 High, 12 Medium Muster korrigiert.`),
ohne den vollständigen Diff auszugeben — User kann `/humanize` für
den vollständigen Diff aufrufen.
