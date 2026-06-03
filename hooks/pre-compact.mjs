#!/usr/bin/env node
/**
 * hooks/pre-compact.mjs — PreCompact Snapshot Hook
 *
 * Schreibt vor jeder Compaction einen Snapshot:
 *   - academic_context.md, literature_state.md, writing_state.md
 *   - vault.export_snapshot() als Tarball nach
 *     ACADEMIC_SNAPSHOTS_DIR/<slug>/<ts>.tgz
 *
 * Protokoll:
 *   - Eingabe: JSON via stdin (Claude Code PreCompact/Notification-Format)
 *   - Exit 0: immer (fail-open, nie blockierend)
 *
 * Konfiguration via Umgebungsvariablen:
 *   ACADEMIC_SNAPSHOTS_DIR  — Zielverzeichnis für Snapshots (default: ~/.academic-research/snapshots)
 *   ACADEMIC_PROJECT_SLUG   — Projekt-Slug (default: "default")
 *   CLAUDE_PROJECT_DIR      — Projekt-Verzeichnis (default: cwd)
 *   VAULT_DB_PATH           — Pfad zur Vault-DB
 */

import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, createWriteStream } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createGzip } from 'node:zlib';
import { pipeline } from 'node:stream/promises';
import { Readable } from 'node:stream';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as os from 'node:os';

const HOOK_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = dirname(HOOK_DIR);

// ---------------------------------------------------------------------------
// Konfiguration
// ---------------------------------------------------------------------------

const SNAPSHOTS_DIR = process.env.ACADEMIC_SNAPSHOTS_DIR
  || join(os.homedir(), '.academic-research', 'snapshots');
const SLUG = process.env.ACADEMIC_PROJECT_SLUG || 'default';
const PROJECT_DIR = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const VAULT_DB = process.env.VAULT_DB_PATH
  || join(os.homedir(), '.academic-research', 'projects', SLUG, 'vault.db');
const VAULT_SRC = REPO_ROOT;

// Zu sichernde State-Dateien (relativ zu PROJECT_DIR)
const STATE_FILES = [
  'academic_context.md',
  'literature_state.md',
  'writing_state.md',
];

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
// Timestamp-Generierung
// ---------------------------------------------------------------------------

/**
 * Gibt Timestamp im Format YYYYMMDD-HHMM zurueck.
 */
function makeTimestamp() {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return [
    now.getFullYear(),
    pad(now.getMonth() + 1),
    pad(now.getDate()),
  ].join('') + '-' + [
    pad(now.getHours()),
    pad(now.getMinutes()),
  ].join('');
}

// ---------------------------------------------------------------------------
// Tarball erstellen (einfache Implementierung ohne externe Deps)
// ---------------------------------------------------------------------------

/**
 * Erstellt einen .tgz-Tarball mit den angegebenen Dateien.
 * Verwendet das GNU-tar CLI.
 */
async function createTarball(outPath, files) {
  // Verzeichnis sicherstellen
  const dir = dirname(outPath);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  // Existierende Dateien filtern
  const existing = files.filter((f) => existsSync(f.src));
  if (existing.length === 0) {
    process.stderr.write('[Snapshot] Warnung: Keine State-Dateien gefunden.\n');
    // Leeren Tarball mit Platzhalter erstellen
    const tmpDir = fs.mkdtempSync(join(os.tmpdir(), 'snapshot-'));
    const placeholder = join(tmpDir, 'snapshot-empty.txt');
    fs.writeFileSync(placeholder, 'Keine State-Dateien vorhanden.\n');
    execFileSync('tar', ['czf', outPath, '-C', tmpDir, 'snapshot-empty.txt'], { timeout: 10000 });
    fs.rmSync(tmpDir, { recursive: true, force: true });
    return;
  }

  // Temporaeres Verzeichnis als Staging
  const tmpDir = fs.mkdtempSync(join(os.tmpdir(), 'snapshot-'));
  try {
    for (const { src, name } of existing) {
      const dest = join(tmpDir, name);
      fs.copyFileSync(src, dest);
    }
    const fileNames = existing.map((f) => f.name);
    execFileSync('tar', ['czf', outPath, '-C', tmpDir, ...fileNames], { timeout: 10000 });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------
// Vault-Snapshot via Python-Subprocess
// ---------------------------------------------------------------------------

/**
 * Exportiert Vault-DB als Tarball. Fail-open wenn Vault fehlt.
 * Gibt Pfad der erstellten Datei zurueck oder null.
 */
function exportVaultSnapshot(outPath) {
  if (!existsSync(VAULT_DB)) {
    process.stderr.write(`[Snapshot] Vault-DB nicht gefunden (${VAULT_DB}). Vault-Snapshot übersprungen.\n`);
    return null;
  }

  const pyCode = [
    'import sys, shutil',
    `sys.path.insert(0, ${JSON.stringify(VAULT_SRC)})`,
    'from academic_vault.server import export_snapshot',
    'import os',
    `result = export_snapshot(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])`,
    'print(result or "")',
  ].join('; ');

  try {
    const outDir = dirname(outPath);
    const slug = SLUG;
    execFileSync('python3', ['-c', pyCode, VAULT_DB, slug, PROJECT_DIR, dirname(outDir)], {
      encoding: 'utf-8',
      timeout: 30000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return outPath;
  } catch (err) {
    process.stderr.write(`[Snapshot] Vault-Export fehlgeschlagen: ${err.message}\n`);
    return null;
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
    // Malformed stdin — trotzdem weitermachen
  }

  // Sicherstellen dass PROJECT_DIR existiert
  if (!existsSync(PROJECT_DIR)) {
    process.stderr.write(`[Snapshot] Warnung: PROJECT_DIR nicht gefunden: ${PROJECT_DIR}\n`);
    process.exit(0);
  }

  const ts = makeTimestamp();
  const slugDir = join(SNAPSHOTS_DIR, SLUG);
  const tarPath = join(slugDir, `${ts}.tgz`);

  // Snapshot-Verzeichnis erstellen
  if (!existsSync(slugDir)) {
    mkdirSync(slugDir, { recursive: true });
  }

  // State-Dateien sammeln
  const files = STATE_FILES.map((name) => ({
    src: join(PROJECT_DIR, name),
    name,
  }));

  // Tarball erstellen
  try {
    await createTarball(tarPath, files);
    process.stderr.write(`[Snapshot] Snapshot erstellt: ${tarPath}\n`);
  } catch (err) {
    process.stderr.write(`[Snapshot] Fehler beim Erstellen des Tarballs: ${err.message}\n`);
  }

  process.exit(0);
}

main().catch((err) => {
  process.stderr.write(`[Snapshot] Unerwarteter Fehler: ${err.message}\n`);
  process.exit(0); // fail-open
});
