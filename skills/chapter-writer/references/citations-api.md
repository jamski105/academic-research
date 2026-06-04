# Zitat-Einbindung via Citations-API

Beim Einweben von Zitaten in Kapitel-Prosa: Quellen-PDFs im
`documents`-Parameter an Claude uebergeben, damit die API die Quellenbindung
erzwingt. Jedes Paraphrase-Segment mit einem `citations[]`-Eintrag nachweisbar.

## Workflow

1. `vault.search("<Kapitelthema>", k=5)` → relevante `paper_id`s
2. Pro paper_id: `vault.find_quotes(paper_id, query, k=3)` → Zitat-Kandidaten
3. Pro Paper: `vault.ensure_file(paper_id)` → `file_id` für Citations-API
4. API-Call mit `documents[]` (file_id), `citations.enabled: true`
5. Output-Text enthält `citations[]`-Blöcke — als Inline-Zitate nach
   Variant-Zitierstil aus `./academic_context.md` rendern.

## Fallback

Gibt `vault.ensure_file()` `None` zurück (kein PDF im Vault), nutze den
Vault-Zitat-Text (`verbatim`) direkt als Prompt-basiertes Zitat ohne
Citations-API-Erzwingung.
