#!/usr/bin/env node
/**
 * hooks/post-tool-use-decisions.mjs — PostToolUse Decision-Log Hook
 *
 * Bei Write-Events auf *.md-Dateien im Projekt-Verzeichnis schreibt
 * eine Zeile in decisions.log:
 *   <ISO-Timestamp> | Write | <relativer-Pfad> | sha256=<hash>
 *
 * Datenschutz (CWE-532):
 *   - KEIN Content-Snippet im Klartext — nur der SHA-256-Hash des Inhalts.
 *   - Logfile wird mit 0600-Permissions geschrieben (nur Owner).
 *   - Rotation bei >10 MB: decisions.log -> decisions.log.1.
 *
 * Protokoll:
 *   - Eingabe: JSON via stdin (Claude Code PostToolUse-Format)
 *   - Exit 0: immer (fail-open, nie blockierend)
 *
 * Konfiguration via Umgebungsvariablen:
 *   ACADEMIC_DECISIONS_LOG  — Pfad zur Log-Datei (default: ~/.academic-research/decisions.log)
 *   CLAUDE_PROJECT_DIR      — Projekt-Verzeichnis (default: cwd)
 */

import { appendFileSync, mkdirSync, existsSync, chmodSync, statSync, renameSync } from 'node:fs';
import { dirname, relative, basename } from 'node:path';
import { createHash } from 'node:crypto';
import * as os from 'node:os';
import * as path from 'node:path';

const DEFAULT_LOG = path.join(os.homedir(), '.academic-research', 'decisions.log');

// Rotation: maximale Logfile-Groesse in Bytes (10 MB), dann -> decisions.log.1
const MAX_LOG_BYTES = 10 * 1024 * 1024;

// ---------------------------------------------------------------------------
// Konfiguration
// ---------------------------------------------------------------------------

const DECISIONS_LOG = process.env.ACADEMIC_DECISIONS_LOG || DEFAULT_LOG;
const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();

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
// Pfad-Check
// ---------------------------------------------------------------------------

/**
 * Gibt true zurueck wenn die Datei eine .md-Datei im Projekt-Verzeichnis ist.
 */
function isMdInProject(filePath) {
  if (!filePath) return false;
  if (!filePath.endsWith('.md')) return false;

  // Normalisiere Pfade fuer Vergleich
  const normalized = path.resolve(filePath);
  const projectResolved = path.resolve(PROJECT_DIR);

  return normalized.startsWith(projectResolved + path.sep) || normalized === projectResolved;
}

// ---------------------------------------------------------------------------
// Log-Zeile schreiben
// ---------------------------------------------------------------------------

/**
 * Rotiert das Logfile, wenn es MAX_LOG_BYTES ueberschreitet.
 * decisions.log -> decisions.log.1 (ueberschreibt eine evtl. vorhandene .1).
 */
function rotateIfNeeded() {
  try {
    if (!existsSync(DECISIONS_LOG)) return;
    const size = statSync(DECISIONS_LOG).size;
    if (size <= MAX_LOG_BYTES) return;
    renameSync(DECISIONS_LOG, `${DECISIONS_LOG}.1`);
  } catch {
    // Rotation ist best-effort — nie blockierend.
  }
}

/**
 * Schreibt eine Zeile in decisions.log.
 * Format: ISO-Timestamp | Write | <relativer-Pfad> | sha256=<hash>
 *
 * Aus Datenschutzgruenden (CWE-532) wird KEIN Content-Snippet im Klartext
 * geloggt. Stattdessen steht der SHA-256-Hash des Inhalts in der Zeile —
 * ausreichend fuer Idempotenz-/Aenderungs-Checks, ohne PII zu leaken.
 */
function writeLogLine(filePath, content) {
  const ts = new Date().toISOString();

  // Relativer Pfad wenn moeglich
  let relPath;
  try {
    relPath = relative(PROJECT_DIR, path.resolve(filePath));
  } catch {
    relPath = basename(filePath);
  }

  // SHA-256-Hash des Inhalts statt Klartext-Snippet (Idempotenz-Check ohne Leak).
  const hash = createHash('sha256').update(content || '', 'utf-8').digest('hex');

  const line = `${ts} | Write | ${relPath} | sha256=${hash}\n`;

  try {
    // Log-Verzeichnis sicherstellen
    const logDir = dirname(DECISIONS_LOG);
    if (!existsSync(logDir)) {
      mkdirSync(logDir, { recursive: true, mode: 0o700 });
    }
    rotateIfNeeded();
    appendFileSync(DECISIONS_LOG, line, 'utf-8');
    // Restriktive Permissions: nur Owner darf lesen/schreiben (0600).
    chmodSync(DECISIONS_LOG, 0o600);
  } catch (err) {
    process.stderr.write(`[Decisions-Log] Fehler beim Schreiben: ${err.message}\n`);
  }
}

// ---------------------------------------------------------------------------
// Haupt-Logik
// ---------------------------------------------------------------------------

async function main() {
  let input = {};
  try {
    const raw = await readStdin();
    if (raw.trim()) {
      input = JSON.parse(raw);
    }
  } catch {
    // Malformed stdin — fail-open
    process.exit(0);
  }

  // Nur Write-Events
  const toolName = input?.tool_name || input?.hook_event_name || '';
  if (toolName !== 'Write') {
    process.exit(0);
  }

  const toolInput = input?.tool_input || {};
  const filePath = toolInput.file_path || '';
  const content = toolInput.content || '';

  // Nur .md-Dateien im Projekt
  if (!isMdInProject(filePath)) {
    process.exit(0);
  }

  writeLogLine(filePath, content);
  process.exit(0);
}

main().catch((err) => {
  process.stderr.write(`[Decisions-Log] Unerwarteter Fehler: ${err.message}\n`);
  process.exit(0); // fail-open
});
