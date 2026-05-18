#!/usr/bin/env node
/**
 * hooks/mid-session-reinforcement.mjs — Mid-Conversation Reinforcement Hook
 *
 * Nicht-blockierender Notification-Hook.
 * Trigger: nach jeder 20. User-Message oder nach Compaction (PostCompact).
 * Liest Top-5 aktive Decisions aus Vault und erinnert Modell als System-Hint.
 * Loest max. 1× pro 20 Messages aus (State-Datei verhindert Duplikate).
 *
 * Protokoll:
 *   - Eingabe: JSON via stdin (Claude Code Notification/PostCompact-Format)
 *   - Ausgabe: Reminder-Text auf stdout (als System-Hint fuer Modell)
 *   - Exit 0: immer (nie blockierend)
 *
 * Konfiguration via Umgebungsvariablen:
 *   VAULT_DB_PATH                 — Pfad zur Vault-DB
 *   ACADEMIC_REINFORCEMENT_STATE  — Pfad zur State-Datei (default: ~/.academic-research/reinforcement-state.json)
 *   ACADEMIC_REINFORCEMENT_N      — Trigger-Interval (default: 20)
 */

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as os from 'node:os';
import * as path from 'node:path';

const HOOK_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = dirname(HOOK_DIR);
const VAULT_SRC = join(REPO_ROOT, 'mcp');

const VAULT_DB = process.env.VAULT_DB_PATH
  || join(os.homedir(), '.academic-research', 'projects', 'default', 'vault.db');

const STATE_FILE = process.env.ACADEMIC_REINFORCEMENT_STATE
  || join(os.homedir(), '.academic-research', 'reinforcement-state.json');

const TRIGGER_N = parseInt(process.env.ACADEMIC_REINFORCEMENT_N || '20', 10);
const MAX_DECISIONS = 5;

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
// State-Verwaltung
// ---------------------------------------------------------------------------

/**
 * Laedt den State aus der State-Datei. Gibt {last_trigger_at: 0} als Default.
 */
function loadState() {
  try {
    if (existsSync(STATE_FILE)) {
      return JSON.parse(readFileSync(STATE_FILE, 'utf-8'));
    }
  } catch {
    // Ignore
  }
  return { last_trigger_at: 0 };
}

/**
 * Speichert den State in die State-Datei.
 */
function saveState(state) {
  try {
    const dir = dirname(STATE_FILE);
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
    writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf-8');
  } catch (err) {
    process.stderr.write(`[Reinforcement] State-Datei konnte nicht gespeichert werden: ${err.message}\n`);
  }
}

// ---------------------------------------------------------------------------
// Vault-Decisions abrufen
// ---------------------------------------------------------------------------

/**
 * Laedt Top-N aktive Decisions aus dem Vault.
 * Gibt leeres Array bei Fehler oder fehlendem Vault (fail-open).
 */
function loadTopDecisions() {
  if (!existsSync(VAULT_DB)) {
    process.stderr.write(`[Reinforcement] Vault-DB nicht gefunden (${VAULT_DB}). Übersprungen.\n`);
    return [];
  }

  const pyCode = [
    'import sys, json',
    `sys.path.insert(0, ${JSON.stringify(VAULT_SRC)})`,
    'from academic_vault.server import list_decisions',
    `decisions = list_decisions(sys.argv[1], active_only=True)`,
    `print(json.dumps(decisions[:${MAX_DECISIONS}]))`,
  ].join('; ');

  try {
    const output = execFileSync('python3', ['-c', pyCode, VAULT_DB], {
      encoding: 'utf-8',
      timeout: 10000,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return JSON.parse(output.trim()) || [];
  } catch (err) {
    process.stderr.write(`[Reinforcement] Vault-Lookup fehlgeschlagen: ${err.message}\n`);
    return [];
  }
}

// ---------------------------------------------------------------------------
// Reminder ausgeben
// ---------------------------------------------------------------------------

/**
 * Gibt System-Hint auf stdout aus.
 */
function printReminder(decisions) {
  const lines = ['[Reinforcement] Aktive Decisions:'];
  for (const d of decisions) {
    const cat = d.category ? `[${d.category}] ` : '';
    lines.push(`  - ${cat}${d.text}`);
  }
  if (decisions.length === 0) {
    lines.push('  (keine aktiven Decisions)');
  }
  // Auf stdout (wird als System-Hint an Modell weitergegeben)
  process.stdout.write(lines.join('\n') + '\n');
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

  const eventName = input?.hook_event_name || '';
  const messageCount = input?.message_count ?? 0;

  const isCompaction = eventName === 'PostCompact';
  const isNthMessage = messageCount > 0 && messageCount % TRIGGER_N === 0;

  if (!isCompaction && !isNthMessage) {
    // Kein Trigger-Bedingung erfuellt
    process.exit(0);
  }

  // State pruefen — max 1× pro 20-Messages-Runde
  const state = loadState();
  const currentRound = Math.floor(messageCount / TRIGGER_N);

  if (!isCompaction && state.last_trigger_at >= currentRound && currentRound > 0) {
    // Bereits in dieser Runde ausgeloest
    process.exit(0);
  }

  // Decisions laden
  const decisions = loadTopDecisions();

  // Reminder ausgeben
  printReminder(decisions);

  // State aktualisieren
  state.last_trigger_at = currentRound;
  saveState(state);

  process.exit(0);
}

main().catch((err) => {
  process.stderr.write(`[Reinforcement] Unerwarteter Fehler: ${err.message}\n`);
  process.exit(0); // fail-open
});
