#!/usr/bin/env node
/**
 * hooks/verbatim-guard.mjs — PreToolUse Verbatim-Validation
 *
 * Blockiert Write-Calls auf kapitel/*.md und *.tex, wenn der Content
 * Anführungszeichen-Spans enthält, die nicht im Vault verifiziert sind.
 *
 * Protokoll:
 *   - Eingabe: JSON via stdin (Claude Code PreToolUse-Format)
 *   - Ausgabe: JSON via stdout (hookSpecificOutput für Block-Hinweis)
 *   - Exit 0: allow (kein Block)
 *   - Exit 2: block (Zitat nicht verifiziert)
 *
 * Bypass: Content enthält <!-- vault-guard: skip --> → immer allow.
 * Fail-open: Bei fehlender Python/Vault-Umgebung → Warnung + allow.
 */

import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

// ---------------------------------------------------------------------------
// Konfiguration
// ---------------------------------------------------------------------------

const HOOK_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = dirname(HOOK_DIR);
const VAULT_SRC = join(REPO_ROOT, 'mcp');
const VAULT_DB = process.env.VAULT_DB_PATH || join(REPO_ROOT, 'vault.db');
// Mindestlänge eines Zitat-Spans (in Zeichen). Muss mit den Regex-Quantifizierern übereinstimmen.
const MIN_QUOTE_LEN = 10;

// ---------------------------------------------------------------------------
// Stdin lesen
// ---------------------------------------------------------------------------

async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf-8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => resolve(data.replace(/^﻿/, '')));
    process.stdin.on('error', reject);
    process.stdin.resume();
  });
}

// ---------------------------------------------------------------------------
// Pfad-Match
// ---------------------------------------------------------------------------

/**
 * Gibt true zurueck wenn der Pfad einer Kapitel-MD- oder LaTeX-Datei entspricht.
 * Patterns: kapitel/*.md | *.tex
 */
function isProtectedPath(filePath) {
  if (!filePath) return false;
  const normalized = filePath.replace(/\\/g, '/');
  if (normalized.endsWith('.tex')) return true;
  // kapitel/<datei>.md — auch bei fuehrendem Slash oder relativen Pfaden
  if (/(?:^|\/)kapitel\/[^/]+\.md$/.test(normalized)) return true;
  return false;
}

// ---------------------------------------------------------------------------
// Quote-Parser
// ---------------------------------------------------------------------------

/**
 * Extrahiert Anführungszeichen-Spans aus dem Content.
 * Unterstuetzte Typen:
 *   "…"   — ASCII double quotes
 *   „…"   — Deutsche Anführungszeichen
 *   «…»   — Guillemets
 *   ``…'' — LaTeX
 *
 * Mindestlänge: MIN_QUOTE_LEN Zeichen (innerer Text).
 * Gibt Array von Strings (innere Texte) zurueck.
 */
function extractQuoteSpans(content) {
  const spans = [];
  const q = MIN_QUOTE_LEN;
  // Jedes Pattern als Konstruktor — dadurch wird lastIndex isoliert pro Durchlauf.
  const patterns = [
    new RegExp(`"([^"]{${q},})"`, 'g'),           // ASCII "…"
    new RegExp(`„([^“]{${q},})“`, 'g'), // Deutsche „…" (U+201E…U+201C)
    new RegExp(`«([^»]{${q},})»`, 'g'), // Guillemets «…» (U+00AB…U+00BB)
    new RegExp(`\`\`([^']{${q},})''`, 'g'),        // LaTeX ``…''
  ];
  for (const r of patterns) {
    let match;
    while ((match = r.exec(content)) !== null) {
      if (match[1]) spans.push(match[1]);
    }
  }
  return spans;
}

// ---------------------------------------------------------------------------
// Vault-Lookup via Python-Subprocess
// ---------------------------------------------------------------------------

/**
 * Sucht verbatim im Vault. Gibt true zurueck wenn ein Treffer gefunden wurde.
 * Bei fehlender Python/Vault-Umgebung: Warnung + true (fail-open).
 */
function lookupInVault(verbatim) {
  // Vault-DB muss existieren (sonst fail-open)
  if (!existsSync(VAULT_DB)) {
    process.stderr.write(
      `[Vault-Guard] Warnung: Vault-DB nicht gefunden (${VAULT_DB}). Bypass aktiv.\n`
    );
    return true; // fail-open
  }

  const pyCode = [
    'import sys, json',
    `sys.path.insert(0, ${JSON.stringify(VAULT_SRC)})`,
    'from academic_vault.server import search_quote_text',
    `hits = search_quote_text(sys.argv[1], sys.argv[2])`,
    'print(json.dumps(hits))',
  ].join('; ');

  try {
    const output = execFileSync('python3', ['-c', pyCode, VAULT_DB, verbatim], {
      encoding: 'utf-8',
      timeout: 10000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    const hits = JSON.parse(output.trim());
    return Array.isArray(hits) && hits.length > 0;
  } catch (err) {
    process.stderr.write(
      `[Vault-Guard] Warnung: Vault-Lookup fehlgeschlagen (${err.message}). Bypass aktiv.\n`
    );
    return true; // fail-open
  }
}

// ---------------------------------------------------------------------------
// Haupt-Logik
// ---------------------------------------------------------------------------

async function main() {
  let input;
  try {
    const raw = await readStdin();
    input = raw ? JSON.parse(raw) : {};
  } catch {
    // Malformed stdin — fail-open
    process.exit(0);
  }

  // Nur Write-Tool-Calls pruefen
  const toolName = input?.tool_name || input?.hook_event_name || '';
  if (toolName !== 'Write') {
    process.exit(0);
  }

  const toolInput = input?.tool_input || {};
  const filePath = toolInput.file_path || '';
  const content = toolInput.content || '';

  // Pfad-Match
  if (!isProtectedPath(filePath)) {
    process.exit(0);
  }

  // Bypass-Flag
  if (content.includes('<!-- vault-guard: skip -->')) {
    process.exit(0);
  }

  // Quote-Spans extrahieren
  const spans = extractQuoteSpans(content);
  if (spans.length === 0) {
    process.exit(0);
  }

  // Jeden Span gegen Vault pruefen
  for (const span of spans) {
    const found = lookupInVault(span);
    if (!found) {
      const truncated = span.length > 80 ? span.slice(0, 77) + '...' : span;
      const msg = [
        `[Vault-Guard] BLOCKIERT: Zitat nicht im Vault verifiziert.`,
        `Zitat: "${truncated}"`,
        `Bitte Zitat über vault.add_quote() oder den quote-extractor einpflegen.`,
        `Bypass: <!-- vault-guard: skip --> im Content ergänzen (nur für Ausnahmefälle).`,
      ].join('\n');
      process.stderr.write(msg + '\n');

      // Claude Code PreToolUse Block-Protokoll: JSON auf stdout + exit 2
      console.log(JSON.stringify({
        decision: 'block',
        reason: msg,
      }));
      process.exit(2);
    }
  }

  // Alle Spans verifiziert
  process.exit(0);
}

main().catch((err) => {
  process.stderr.write(`[Vault-Guard] Fehler: ${err.message}\n`);
  process.exit(0); // fail-open bei unerwartetem Fehler
});
