# Eval · verbatim-guard

Validiert den `hooks/verbatim-guard.mjs`-PreToolUse-Hook gegen 10 Test-Cases
(5 echte Vault-Quotes, 5 erfundene Zitate).

## Acceptance Criteria

| Kriterium | Ziel |
|---|---|
| Echte Quotes (Cases 1–5) | 100 % pass |
| Erfundene Quotes (Cases 6–10) | 100 % block |
| False-Positive-Rate | < 5 % |

## Dateien

| Datei | Inhalt |
|---|---|
| `cases.json` | 10 Test-Cases mit `quote_text`, `in_vault`, `expected` |
| `runner.py` | Eval-Runner — befuellt Temp-DB, prueft Vault-Lookup |
| `README.md` | Diese Datei |

## Ausfuehren

### Vault-Lookup-Test (Python-Runner)

Prueft `vault.search_quote_text()` direkt:

```bash
cd /path/to/academic-research
python3 evals/verbatim-guard/runner.py
```

Erwartet:
```
[OK] Case 1 (real): expected=pass, actual=pass, hits=1
...
[OK] Case 10 (invented): expected=block, actual=block, hits=0
Ergebnis: 10/10 korrekt (0 Fehler)
False-Positive-Rate: 0/5 = 0.0% (AC: < 5 %)
✅ Alle Eval-Cases bestanden.
```

### Smoke-Test des Hooks (1 Case)

Prueft den vollstaendigen Hook-Flow (Pfad-Match + Parser + Vault-Lookup):

**Voraussetzung:** `VAULT_DB_PATH` muss auf eine DB mit Case 1–5 zeigen.
Den Runner mit `--setup-only`-Flag benutzen oder manuell befuellen.

```bash
# Case 1: echtes Zitat → expect exit 0 (allow)
echo '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "kapitel/01-einleitung.md",
    "content": "Wie Kant schreibt: \"Die Digitalisierung verändert grundlegend die Art und Weise, wie Wissen produziert und verbreitet wird.\""
  }
}' | VAULT_DB_PATH=/tmp/eval-vault.db node hooks/verbatim-guard.mjs
echo "Exit: $?"

# Case 6: erfundenes Zitat → expect exit 2 (block)
echo '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "kapitel/01-einleitung.md",
    "content": "\"Die kumulative Wissensakkumulation folgt einer exponentiellen Wachstumskurve seit 1950.\""
  }
}' | VAULT_DB_PATH=/tmp/eval-vault.db node hooks/verbatim-guard.mjs
echo "Exit: $?"
```

## Case-Format

```json
{
  "id": 1,
  "type": "real",
  "description": "Beschreibung des Cases",
  "quote_text": "Der Zitat-Text ohne Anführungszeichen",
  "in_vault": true,
  "expected": "pass"
}
```

| Feld | Werte |
|---|---|
| `type` | `"real"` oder `"invented"` |
| `in_vault` | `true` wenn im Vault gespeichert |
| `expected` | `"pass"` (allow) oder `"block"` |

## Hinzufuegen neuer Cases

1. `cases.json` ergaenzen (ID fortlaufend).
2. `runner.py` laufen lassen — alle Cases muessen gruen sein.
3. Echte Quotes: vorher via `vault.add_quote()` oder `quote-extractor` einpflegen.
