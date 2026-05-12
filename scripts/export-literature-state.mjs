#!/usr/bin/env node
/**
 * export-literature-state.mjs
 *
 * Generiert ./literature_state.md als read-only Snapshot-Export aus dem Vault.
 * Aufruf: node scripts/export-literature-state.mjs [--output ./literature_state.md]
 *
 * Voraussetzungen:
 *   - academic-vault MCP-Server läuft oder vault.db ist lokal erreichbar
 *   - VAULT_DB_PATH gesetzt oder vault.db im CWD
 *
 * Hinweis: Dieses Skript liest den Vault direkt über das Python-Modul
 * (mcp.academic_vault.db), da kein MCP-HTTP-Client in diesem Repo verfügbar ist.
 * In einer MCP-Umgebung können stattdessen vault.search() + vault.get_paper()
 * Tool-Calls verwendet werden.
 */

import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

// --- Konfiguration ---

const OUTPUT_PATH =
  process.argv[2] === "--output"
    ? resolve(process.argv[3] ?? "./literature_state.md")
    : resolve("./literature_state.md");

const VAULT_DB = process.env.VAULT_DB_PATH ?? "vault.db";

// --- Hilfsfunktionen ---

/**
 * Führt einen Python3-Einzeiler aus und gibt das geparste JSON-Ergebnis zurück.
 * Bei Fehler: gibt null zurück und loggt die Fehlermeldung.
 */
function runPython(code) {
  try {
    const escaped = code
      .replace(/\\/g, "\\\\")
      .replace(/"/g, '\\"')
      .replace(/\n/g, "\\n");
    const result = execSync(`python3 -c "${escaped}"`, {
      env: { ...process.env, VAULT_DB_PATH: VAULT_DB },
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    return JSON.parse(result.trim());
  } catch (e) {
    const msg = e.stderr?.toString().trim() ?? e.message;
    console.error("[export-literature-state] Python-Fehler:", msg);
    return null;
  }
}

/**
 * Gibt alle Paper aus dem Vault zurück (neueste zuerst).
 */
function getAllPapers() {
  return runPython(`
import sys, json
sys.path.insert(0, '.')
try:
    from mcp.academic_vault.db import VaultDB
    conn = VaultDB._open('${VAULT_DB.replace(/'/g, "\\'")}')
    rows = conn.execute(
        'SELECT paper_id, csl_json, pdf_path, file_id, type FROM papers ORDER BY added_at DESC'
    ).fetchall()
    conn.close()
    print(json.dumps([dict(r) for r in rows]))
except Exception as e:
    print(json.dumps([]))
`);
}

/**
 * Gibt die Anzahl gespeicherter Zitate für ein Paper zurück.
 */
function getQuoteCount(paperId) {
  const safe = paperId.replace(/'/g, "\\'");
  return runPython(`
import sys, json
sys.path.insert(0, '.')
try:
    from mcp.academic_vault.db import VaultDB
    conn = VaultDB._open('${VAULT_DB.replace(/'/g, "\\'")}')
    row = conn.execute('SELECT COUNT(*) AS cnt FROM quotes WHERE paper_id = ?', ('${safe}',)).fetchone()
    conn.close()
    print(json.dumps(row['cnt'] if row else 0))
except Exception as e:
    print(json.dumps(0))
`);
}

/**
 * Formatiert einen Paper-Datensatz als Markdown-Abschnitt.
 */
function formatPaperEntry(paper, quoteCount) {
  let csl = {};
  try {
    csl = JSON.parse(paper.csl_json);
  } catch {
    // CSL-JSON nicht parsebar — Fallback auf paper_id
  }

  const title = csl.title ?? paper.paper_id;
  const authors =
    (csl.author ?? [])
      .map((a) => [a.family, a.given ? `, ${a.given}` : ""].filter(Boolean).join(""))
      .join("; ") || "Unbekannt";
  const year = csl.issued?.["date-parts"]?.[0]?.[0] ?? "o.J.";
  const doi = csl.DOI ?? paper.doi ?? "";
  const pdfStatus = paper.file_id
    ? `gecacht (file_id: \`${paper.file_id.slice(0, 8)}…\`)`
    : paper.pdf_path
    ? `lokal: \`${paper.pdf_path}\``
    : "kein PDF";

  return [
    `### ${paper.paper_id}`,
    "",
    `- **Titel:** ${title}`,
    `- **Autoren:** ${authors}`,
    `- **Jahr:** ${year}`,
    doi ? `- **DOI:** ${doi}` : null,
    `- **PDF-Status:** ${pdfStatus}`,
    `- **Zitate im Vault:** ${quoteCount ?? 0}`,
    "",
  ]
    .filter((line) => line !== null)
    .join("\n");
}

// --- Hauptprogramm ---

console.log(`[export-literature-state] Lese Vault: ${VAULT_DB}`);

const papers = getAllPapers();

if (!papers || papers.length === 0) {
  console.warn(
    "[export-literature-state] Keine Paper im Vault gefunden. Schreibe leeren Snapshot."
  );
  const empty = [
    "# Literatur-Snapshot",
    "",
    `_Generiert via \`node scripts/export-literature-state.mjs\` — ${new Date().toISOString()}_`,
    "",
    "> Vault enthält noch keine Paper.",
    "> Bitte zuerst \`vault.add_paper()\` aufrufen.",
    "",
  ].join("\n");
  writeFileSync(OUTPUT_PATH, empty, "utf-8");
  console.log(`[export-literature-state] Leerer Snapshot geschrieben: ${OUTPUT_PATH}`);
  process.exit(0);
}

const header = [
  "# Literatur-Snapshot",
  "",
  `> **Read-only Export** aus dem Vault — generiert ${new Date().toISOString()}`,
  `> Vault: \`${VAULT_DB}\` · ${papers.length} Paper`,
  "> Zum Regenerieren: `node scripts/export-literature-state.mjs`",
  "> **Nicht manuell bearbeiten** — Änderungen werden beim nächsten Export überschrieben.",
  "",
  "---",
  "",
].join("\n");

const entries = papers
  .map((paper) => {
    const quoteCount = getQuoteCount(paper.paper_id);
    return formatPaperEntry(paper, quoteCount);
  })
  .join("\n");

writeFileSync(OUTPUT_PATH, header + entries, "utf-8");
console.log(
  `[export-literature-state] Snapshot geschrieben: ${OUTPUT_PATH} (${papers.length} Paper)`
);
