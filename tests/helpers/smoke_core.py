"""smoke_core — gemeinsame End-to-End-Smoke-Logik.

Wird von ZWEI Deliverables geteilt:
  * ``tests/test_smoke_e2e.py``  — pytest-Wrapper (CI-grün).
  * ``scripts/smoke.py``         — eigenständiger PASS/FAIL-Reporter.

Jede ``check_*``-Funktion ist eine eigenständige, deterministische Prüfung
OHNE echtes Netzwerk. Sie wirft bei Fehler eine ``AssertionError`` (für
pytest) bzw. wird vom Standalone-Runner in PASS/FAIL übersetzt.

Abgedeckte Bereiche (siehe Modul-Sektionen):
  A) MCP-Server-Lifecycle (echter Subprozess via mcp.client.stdio).
  B) Hooks (echte node-Subprozesse).
  C) Struktur-/Integritäts-Gate (plugin/marketplace/skills/commands/agents).
  D) Scripts (Importierbarkeit + reine Funktion auf Fixture).

Design-Entscheidung: KEIN ``os.environ`` in den MCP-/Hook-Subprozess spreaden
(es gibt einen Secrets-Schutz-Hook, der das blockt). Nur eine minimale,
explizite Env (PATH, HOME, PYTHONPATH, VAULT_DB_PATH, SQLITE_VEC_PATH).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Pfade / Konstanten
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_DIR = REPO_ROOT / "hooks"
SKILLS_DIR = REPO_ROOT / "skills"
COMMANDS_DIR = REPO_ROOT / "commands"
AGENTS_DIR = REPO_ROOT / "agents"
SCRIPTS_DIR = REPO_ROOT / "scripts"
SERVER_PY = REPO_ROOT / "academic_vault" / "server.py"
README = REPO_ROOT / "README.md"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"

EXPECTED_TOOL_COUNT = 33

# venv-Python, das den MCP-Server beherbergt.
VENV_PYTHON = Path.home() / ".academic-research" / "venv" / "bin" / "python"

# Skill-/Command-/Agent-Ordner, die KEINE Entrypoints sind (ausgenommen).
NON_ENTRYPOINT_DIRS = {"_common", "references"}

# Tool-Name-Regex (autoritative Quelle = server.py).
TOOL_NAME_RE = re.compile(r'@mcp\.tool\(name="(vault\.[a-z_]+)"\)')


# ---------------------------------------------------------------------------
# Subprozess-Env (Secrets-Schutz-konform: kein os.environ-Spread)
# ---------------------------------------------------------------------------


def _minimal_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Baut eine minimale, explizite Env für Subprozesse.

    Spreadet bewusst NICHT ``os.environ`` — ein Secrets-Schutz-Hook würde das
    blocken, und der MCP-Server braucht nur diese wenigen Variablen.
    """
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": str(REPO_ROOT),
    }
    if extra:
        env.update(extra)
    return env


# ---------------------------------------------------------------------------
# Frontmatter-Parser (minimal, ohne PyYAML-Abhängigkeit)
# ---------------------------------------------------------------------------


def _parse_frontmatter_keys(md_path: Path) -> set[str]:
    """Liest die Top-Level-Keys aus dem YAML-Frontmatter einer Markdown-Datei.

    Erkennt ``--- ... ---`` am Dateianfang und sammelt ``key:``-Zeilen auf
    Spalte 0 (Top-Level). Verschachtelte Keys (eingerückt) werden ignoriert.
    """
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return set()
    # Frontmatter zwischen erstem und zweitem '---'.
    parts = text.split("---", 2)
    if len(parts) < 3:
        return set()
    fm = parts[1]
    keys: set[str] = set()
    for line in fm.splitlines():
        # Nur Top-Level-Keys (keine Einrückung, keine Listen-/Kommentarzeile).
        if not line or line[0] in (" ", "\t", "#", "-"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:", line)
        if m:
            keys.add(m.group(1))
    return keys


# ---------------------------------------------------------------------------
# MCP-Subprozess-Hilfen
# ---------------------------------------------------------------------------


def _tool_payload(result: Any) -> Any:
    """Extrahiert die Nutzlast aus einem CallToolResult robust.

    FastMCP wrappt skalare/Listen-Returns in ``structuredContent={"result": …}``
    und liefert dict-Returns direkt. Listen erzeugen mehrere content-Items, daher
    ist ``structuredContent`` die verlässlichste Quelle.
    """
    sc = getattr(result, "structuredContent", None)
    if isinstance(sc, dict) and set(sc.keys()) == {"result"}:
        return sc["result"]
    if isinstance(sc, dict) and sc:
        return sc
    content = getattr(result, "content", None)
    if content and getattr(content[0], "text", None):
        try:
            return json.loads(content[0].text)
        except (ValueError, TypeError):
            return content[0].text
    return None


async def _run_mcp_session(db_path: str, work_dir: str) -> dict[str, Any]:
    """Startet den MCP-Server als Subprozess und führt den vollen Round-Trip aus.

    Gibt ein dict mit Ergebnissen/Flags zurück, das die ``check_mcp_*``-Funktionen
    asserten. Wirft bei Verbindungs-/Tool-Fehlern.
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = _minimal_env({"VAULT_DB_PATH": db_path, "SQLITE_VEC_PATH": ""})
    params = StdioServerParameters(
        command=str(VENV_PYTHON),
        args=["-m", "academic_vault.server"],
        cwd=str(REPO_ROOT),
        env=env,
    )

    out: dict[str, Any] = {}
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # --- list_tools: exakt 33 -------------------------------------
            listed = await session.list_tools()
            out["tool_names"] = sorted(t.name for t in listed.tools)

            async def call(name: str, args: dict | None = None):
                return await session.call_tool(name, args or {})

            # --- Papers: add -> get -> search -> stats --------------------
            csl = json.dumps(
                {
                    "type": "article-journal",
                    "title": "Quantum Smoke Theory",
                    "author": [{"family": "Tester"}],
                }
            )
            r = await call(
                "vault.add_paper",
                {"paper_id": "smoke-p1", "csl_json": csl, "provenance": "smoke-suite"},
            )
            out["add_paper_error"] = r.isError
            out["get_paper"] = _tool_payload(
                await call("vault.get_paper", {"paper_id": "smoke-p1"})
            )
            out["search"] = _tool_payload(await call("vault.search", {"query": "Quantum"}))
            out["stats"] = _tool_payload(await call("vault.stats"))

            # --- list_papers_by_provenance --------------------------------
            out["provenance"] = _tool_payload(
                await call("vault.list_papers_by_provenance", {"provenance": "smoke-suite"})
            )

            # --- Chapter ---------------------------------------------------
            ch_csl = json.dumps({"type": "chapter", "title": "Kapitel Eins"})
            out["add_chapter"] = _tool_payload(
                await call(
                    "vault.add_chapter",
                    {"parent_paper_id": "smoke-p1", "chapter_number": 1, "csl_json": ch_csl},
                )
            )

            # --- Quotes: add -> search_text -> find -> get -----------------
            verbatim = "Dies ist ein eindeutig verifizierbares Smoke-Test-Zitat im Vault"
            qid = _tool_payload(
                await call(
                    "vault.add_quote",
                    {"paper_id": "smoke-p1", "verbatim": verbatim, "extraction_method": "manual"},
                )
            )
            out["quote_id"] = qid
            out["search_quote_text"] = _tool_payload(
                await call("vault.search_quote_text", {"verbatim": "verifizierbares Smoke"})
            )
            out["find_quotes"] = _tool_payload(
                await call("vault.find_quotes", {"paper_id": "smoke-p1"})
            )
            out["get_quote"] = _tool_payload(await call("vault.get_quote", {"quote_id": qid}))

            # --- Figures: add -> get -> list -------------------------------
            fid = _tool_payload(
                await call(
                    "vault.add_figure",
                    {"paper_id": "smoke-p1", "page": 7, "caption": "Abbildung Smoke"},
                )
            )
            out["figure_id"] = fid
            out["get_figure"] = _tool_payload(await call("vault.get_figure", {"figure_id": fid}))
            out["list_figures"] = _tool_payload(
                await call("vault.list_figures", {"paper_id": "smoke-p1"})
            )

            # --- Page-Offset: set -> get_printed_page ----------------------
            await call("vault.set_page_offset", {"paper_id": "smoke-p1", "offset": 12})
            out["printed_page"] = _tool_payload(
                await call("vault.get_printed_page", {"paper_id": "smoke-p1", "pdf_page": 20})
            )

            # --- Decisions: add -> list -> supersede -----------------------
            d1 = _tool_payload(
                await call("vault.add_decision", {"category": "scope", "text": "Nur DACH-Quellen"})
            )
            d2 = _tool_payload(
                await call("vault.add_decision", {"category": "scope", "text": "Auch EU-Quellen"})
            )
            await call("vault.supersede_decision", {"decision_id": d1, "superseded_by": d2})
            out["list_decisions"] = _tool_payload(await call("vault.list_decisions"))

            # --- Excluded sources: add -> is_excluded -> list --------------
            await call(
                "vault.add_excluded_source", {"paper_id": "smoke-bad", "reason": "off-topic"}
            )
            out["is_excluded"] = _tool_payload(
                await call("vault.is_excluded", {"paper_id": "smoke-bad"})
            )
            out["list_excluded"] = _tool_payload(await call("vault.list_excluded_sources"))

            # --- Risk-of-Bias: add -> list ---------------------------------
            await call(
                "vault.add_risk_of_bias",
                {
                    "paper_id": "smoke-p1",
                    "study_type": "rct",
                    "domain_scores": json.dumps({"randomization": "low"}),
                },
            )
            out["list_rob"] = _tool_payload(
                await call("vault.list_risk_of_bias", {"paper_id": "smoke-p1"})
            )

            # --- Score-Snapshots: add -> history ---------------------------
            await call(
                "vault.add_score_snapshot",
                {
                    "paper_id": "smoke-p1",
                    "session_id": "sess-1",
                    "scores": json.dumps({"relevance": 5, "quality": 4}),
                },
            )
            out["score_history"] = _tool_payload(
                await call("vault.get_score_history", {"paper_id": "smoke-p1"})
            )

            # --- Material Passport: export -> lock -> is_locked ------------
            mp = _tool_payload(
                await call(
                    "vault.export_material_passport", {"slug": "smoke", "output_dir": work_dir}
                )
            )
            out["passport_path"] = mp
            out["passport_exists"] = bool(isinstance(mp, str) and Path(mp).exists())
            await call("vault.lock_passport", {"slug": "smoke"})
            out["is_locked"] = _tool_payload(await call("vault.is_locked", {"slug": "smoke"}))

            # --- Snapshot: export -> restore -------------------------------
            snap_base = str(Path(work_dir) / "snapshots")
            (Path(work_dir) / "academic_context.md").write_text("ctx-smoke", encoding="utf-8")
            tgz = _tool_payload(
                await call(
                    "vault.export_snapshot",
                    {"slug": "smoke", "project_dir": work_dir, "snapshots_dir": snap_base},
                )
            )
            out["snapshot_tgz"] = tgz
            restored = False
            if isinstance(tgz, str) and tgz:
                ts = Path(tgz).stem
                restore_dir = str(Path(work_dir) / "restore")
                ok = _tool_payload(
                    await call(
                        "vault.restore_snapshot",
                        {
                            "slug": "smoke",
                            "ts": ts,
                            "snapshots_dir": snap_base,
                            "target_dir": restore_dir,
                        },
                    )
                )
                restored = bool(ok) and (Path(restore_dir) / "academic_context.md").exists()
            out["snapshot_restored"] = restored

            # --- Negativtest: malformed csl_json MUSS fehlschlagen ---------
            bad = await call(
                "vault.add_paper", {"paper_id": "smoke-bad-json", "csl_json": "{not valid json"}
            )
            out["malformed_csl_error"] = bad.isError

    return out


def run_mcp_roundtrip() -> dict[str, Any]:
    """Synchroner Wrapper: temp-DB + Cleanup, gibt das Ergebnis-dict zurück."""
    with tempfile.TemporaryDirectory(prefix="smoke-mcp-") as tmp:
        db_path = str(Path(tmp) / "vault.db")
        return asyncio.run(_run_mcp_session(db_path, tmp))


# ---------------------------------------------------------------------------
# Hook-Subprozess-Hilfen
# ---------------------------------------------------------------------------


def _run_node_hook(
    hook_name: str, stdin_payload: str, env: dict[str, str]
) -> subprocess.CompletedProcess:
    """Führt einen node-Hook als Subprozess aus."""
    return subprocess.run(
        ["node", str(HOOKS_DIR / hook_name)],
        input=stdin_payload,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


# ===========================================================================
# A) MCP-Server-Lifecycle
# ===========================================================================


def check_mcp_lifecycle(state: dict[str, Any]) -> None:
    """Server startet, initialize + list_tools liefern exakt 33 Tools."""
    names = state["tool_names"]
    assert (
        len(names) == EXPECTED_TOOL_COUNT
    ), f"Erwartet {EXPECTED_TOOL_COUNT} Tools via list_tools, erhielt {len(names)}: {names}"
    for required in (
        "vault.add_paper",
        "vault.search",
        "vault.stats",
        "vault.export_snapshot",
        "vault.supersede_decision",
    ):
        assert required in names, f"{required} fehlt in list_tools"


def check_mcp_papers(state: dict[str, Any]) -> None:
    """add_paper -> get_paper -> search -> stats round-trip."""
    assert state["add_paper_error"] is False, "add_paper meldete unerwartet isError"
    paper = state["get_paper"]
    assert (
        isinstance(paper, dict) and paper.get("paper_id") == "smoke-p1"
    ), f"get_paper lieferte unplausibles Ergebnis: {paper}"
    assert paper.get("type") == "article-journal"
    search = state["search"]
    assert isinstance(search, list) and any(
        h.get("paper_id") == "smoke-p1" for h in search
    ), f"search fand das eingefügte Paper nicht: {search}"
    stats = state["stats"]
    assert (
        isinstance(stats, dict) and stats.get("paper_count", 0) >= 1
    ), f"stats unplausibel: {stats}"


def check_mcp_provenance(state: dict[str, Any]) -> None:
    """list_papers_by_provenance findet das getaggte Paper."""
    prov = state["provenance"]
    assert isinstance(prov, list) and any(
        p.get("paper_id") == "smoke-p1" for p in prov
    ), f"Provenance-Audit fand smoke-p1 nicht: {prov}"


def check_mcp_chapter(state: dict[str, Any]) -> None:
    """add_chapter gibt eine Kind-paper_id zurück."""
    ch = state["add_chapter"]
    assert ch == "smoke-p1-ch1", f"add_chapter lieferte unerwartete paper_id: {ch}"


def check_mcp_quotes(state: dict[str, Any]) -> None:
    """add_quote -> search_quote_text -> find_quotes -> get_quote."""
    assert isinstance(state["quote_id"], str) and state["quote_id"], "add_quote gab keine quote_id"
    sqt = state["search_quote_text"]
    assert isinstance(sqt, list) and len(sqt) >= 1, f"search_quote_text fand nichts: {sqt}"
    fq = state["find_quotes"]
    assert isinstance(fq, list) and any(
        q.get("quote_id") == state["quote_id"] for q in fq
    ), f"find_quotes lieferte das Zitat nicht: {fq}"
    gq = state["get_quote"]
    assert (
        isinstance(gq, dict) and gq.get("quote_id") == state["quote_id"]
    ), f"get_quote unplausibel: {gq}"


def check_mcp_figures(state: dict[str, Any]) -> None:
    """add_figure -> get_figure -> list_figures."""
    fid = state["figure_id"]
    assert isinstance(fid, str) and fid, "add_figure gab keine figure_id"
    gf = state["get_figure"]
    assert isinstance(gf, dict) and gf.get("figure_id") == fid, f"get_figure unplausibel: {gf}"
    lf = state["list_figures"]
    assert isinstance(lf, list) and any(
        f.get("figure_id") == fid for f in lf
    ), f"list_figures lieferte die Figure nicht: {lf}"


def check_mcp_page_offset(state: dict[str, Any]) -> None:
    """set_page_offset + get_printed_page: 20 - 12 = 8."""
    assert (
        state["printed_page"] == 8
    ), f"get_printed_page erwartete 8 (20-12), erhielt {state['printed_page']}"


def check_mcp_decisions(state: dict[str, Any]) -> None:
    """add_decision x2 -> supersede -> list (nur aktive)."""
    ld = state["list_decisions"]
    assert isinstance(ld, list), f"list_decisions kein list: {ld}"
    texts = {d.get("text") for d in ld}
    # Die superseded Decision (Nur DACH-Quellen) darf bei active_only nicht erscheinen.
    assert "Auch EU-Quellen" in texts, f"Nachfolge-Decision fehlt: {texts}"
    assert (
        "Nur DACH-Quellen" not in texts
    ), f"Superseded Decision noch in active_only-Liste: {texts}"


def check_mcp_excluded(state: dict[str, Any]) -> None:
    """add_excluded_source -> is_excluded -> list_excluded_sources."""
    assert state["is_excluded"] is True, f"is_excluded sollte True sein: {state['is_excluded']}"
    le = state["list_excluded"]
    assert isinstance(le, list) and any(
        e.get("paper_id") == "smoke-bad" for e in le
    ), f"list_excluded_sources fand den Eintrag nicht: {le}"


def check_mcp_risk_of_bias(state: dict[str, Any]) -> None:
    """add_risk_of_bias -> list_risk_of_bias."""
    rob = state["list_rob"]
    assert isinstance(rob, list) and len(rob) >= 1, f"list_risk_of_bias leer: {rob}"
    assert any(r.get("paper_id") == "smoke-p1" for r in rob), f"RoB-Eintrag fehlt: {rob}"


def check_mcp_scores(state: dict[str, Any]) -> None:
    """add_score_snapshot -> get_score_history."""
    sh = state["score_history"]
    assert isinstance(sh, list) and len(sh) >= 1, f"score_history leer: {sh}"
    assert "scores_json" in sh[0], f"score_history-Eintrag ohne scores_json: {sh[0]}"


def check_mcp_passport(state: dict[str, Any]) -> None:
    """export_material_passport -> lock_passport -> is_locked."""
    assert state[
        "passport_exists"
    ], f"material-passport.json wurde nicht erzeugt: {state['passport_path']}"
    assert state["is_locked"] is True, f"is_locked sollte True sein: {state['is_locked']}"


def check_mcp_snapshot(state: dict[str, Any]) -> None:
    """export_snapshot -> restore_snapshot (Datei wiederhergestellt)."""
    assert (
        isinstance(state["snapshot_tgz"], str) and state["snapshot_tgz"]
    ), "export_snapshot gab keinen Pfad zurück"
    assert (
        state["snapshot_restored"] is True
    ), "restore_snapshot stellte academic_context.md nicht wieder her"


def check_mcp_malformed_csl(state: dict[str, Any]) -> None:
    """Negativtest: malformed csl_json MUSS einen Fehler liefern (#213/#232)."""
    assert (
        state["malformed_csl_error"] is True
    ), "add_paper mit malformed csl_json hätte fehlschlagen müssen (strikte Validierung)"


# ===========================================================================
# B) Hooks
# ===========================================================================


def check_hook_verbatim_guard() -> None:
    """verbatim-guard: exaktes Vault-Zitat erlaubt, erfundenes blockiert."""
    from academic_vault.server import add_paper, add_quote

    with tempfile.TemporaryDirectory(prefix="smoke-guard-") as tmp:
        proj = Path(tmp) / "proj"
        (proj / "kapitel").mkdir(parents=True)
        db = str(proj / "vault.db")

        add_paper(db, "g1", json.dumps({"type": "article-journal", "title": "T"}))
        verbatim = "Wissenschaft ist die Kunst des Moeglichen im akademischen Kontext"
        add_quote(db, "g1", verbatim, "manual")

        venv_bin = str(VENV_PYTHON.parent)
        env = {
            "PATH": venv_bin + os.pathsep + os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "VAULT_DB_PATH": db,
            "CLAUDE_PROJECT_DIR": str(proj),
        }
        chapter_file = str(proj / "kapitel" / "x.md")

        def write_payload(content: str) -> str:
            return json.dumps(
                {
                    "tool_name": "Write",
                    "tool_input": {"file_path": chapter_file, "content": content},
                }
            )

        # (a) exaktes Zitat -> ERLAUBT (exit 0)
        allow = _run_node_hook(
            "verbatim-guard.mjs", write_payload(f'Im Text steht: "{verbatim}" als Beleg.'), env
        )
        assert allow.returncode == 0, (
            f"verbatim-guard blockierte ein VERIFIZIERTES Zitat (rc={allow.returncode}). "
            f"stderr: {allow.stderr[:300]}"
        )

        # (b) erfundenes Zitat -> BLOCKIERT (exit 2 + decision:block)
        invented = "Dieses Zitat wurde frei erfunden und niemals in den Vault eingepflegt"
        block = _run_node_hook(
            "verbatim-guard.mjs", write_payload(f'Angeblich: "{invented}" — falsch.'), env
        )
        assert block.returncode == 2, (
            f"verbatim-guard blockierte ein ERFUNDENES Zitat NICHT (rc={block.returncode}). "
            f"stdout: {block.stdout[:200]} stderr: {block.stderr[:200]}"
        )
        decision = json.loads(block.stdout.strip())
        assert decision.get("decision") == "block", f"Block-Payload ohne decision:block: {decision}"


def check_hook_decisions_log() -> None:
    """post-tool-use-decisions: gehashte Log-Zeile + 0600-Perms."""
    with tempfile.TemporaryDirectory(prefix="smoke-declog-") as tmp:
        proj = Path(tmp) / "proj"
        proj.mkdir()
        log_file = str(Path(tmp) / "decisions.log")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "ACADEMIC_DECISIONS_LOG": log_file,
            "CLAUDE_PROJECT_DIR": str(proj),
        }
        md_file = str(proj / "notes.md")
        payload = json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": md_file, "content": "Entscheidung X"},
            }
        )
        proc = _run_node_hook("post-tool-use-decisions.mjs", payload, env)
        assert proc.returncode == 0, f"decisions-Hook exit != 0: {proc.stderr[:200]}"
        assert Path(log_file).exists(), "decisions.log wurde nicht geschrieben"

        mode = Path(log_file).stat().st_mode & 0o777
        assert mode == 0o600, f"decisions.log hat falsche Perms: {oct(mode)} (erwartet 0o600)"

        line = Path(log_file).read_text(encoding="utf-8").strip()
        assert "sha256=" in line, f"Log-Zeile ohne sha256-Hash: {line}"
        # KEIN Klartext-Content (Datenschutz CWE-532).
        assert "Entscheidung X" not in line, f"Klartext-Content im Log geleakt: {line}"
        assert "| Write |" in line, f"Tool-Name fehlt in Log-Zeile: {line}"


def check_hook_no_crash() -> None:
    """pre-compact + mid-session-reinforcement: leerer Input -> exit 0, kein Crash."""
    with tempfile.TemporaryDirectory(prefix="smoke-nocrash-") as tmp:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
            "CLAUDE_PROJECT_DIR": tmp,
            "ACADEMIC_SNAPSHOTS_DIR": str(Path(tmp) / "snaps"),
        }
        for hook, payload in (
            ("pre-compact.mjs", "{}"),
            ("mid-session-reinforcement.mjs", ""),
        ):
            proc = _run_node_hook(hook, payload, env)
            assert proc.returncode == 0, (
                f"{hook} crashte mit Exit {proc.returncode} bei leerem Input. "
                f"stderr: {proc.stderr[:300]}"
            )


# ===========================================================================
# C) Struktur-/Integritäts-Gate
# ===========================================================================


def check_plugin_marketplace_consistency() -> None:
    """plugin.json + marketplace.json: valides JSON, Version 6.5.x, Name konsistent."""
    plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    market = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))

    assert (
        plugin.get("name") == "academic-research"
    ), f"plugin.json name unerwartet: {plugin.get('name')}"
    assert (
        market.get("name") == "academic-research"
    ), f"marketplace.json name unerwartet: {market.get('name')}"

    p_ver = plugin.get("version", "")
    assert re.match(r"^6\.5\.\d+$", p_ver), f"plugin.json Version nicht 6.5.x: {p_ver}"

    plugins = market.get("plugins", [])
    assert plugins, "marketplace.json hat keine plugins-Liste"
    mp_plugin = plugins[0]
    assert (
        mp_plugin.get("name") == "academic-research"
    ), f"marketplace-Plugin-Name unerwartet: {mp_plugin.get('name')}"
    assert (
        mp_plugin.get("version") == p_ver
    ), f"Version-Drift: plugin.json={p_ver} vs marketplace.json={mp_plugin.get('version')}"


def _iter_entrypoint_dirs(base: Path):
    for child in sorted(base.iterdir()):
        if child.is_dir() and child.name not in NON_ENTRYPOINT_DIRS:
            yield child


def check_skills_frontmatter() -> None:
    """Jede skills/*/SKILL.md hat name + description im Frontmatter."""
    missing: list[str] = []
    for skill_dir in _iter_entrypoint_dirs(SKILLS_DIR):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            missing.append(f"{skill_dir.name}: SKILL.md fehlt")
            continue
        keys = _parse_frontmatter_keys(skill_md)
        for req in ("name", "description"):
            if req not in keys:
                missing.append(f"{skill_dir.name}: Frontmatter-Key '{req}' fehlt")
    assert not missing, "Skill-Frontmatter-Probleme:\n  " + "\n  ".join(missing)


def check_commands_frontmatter() -> None:
    """Jedes commands/*.md hat description im Frontmatter."""
    missing: list[str] = []
    for cmd in sorted(COMMANDS_DIR.glob("*.md")):
        keys = _parse_frontmatter_keys(cmd)
        if "description" not in keys:
            missing.append(f"{cmd.name}: 'description' fehlt")
    assert not missing, "Command-Frontmatter-Probleme:\n  " + "\n  ".join(missing)


def check_agents_frontmatter() -> None:
    """Jedes agents/*.md hat name + description im Frontmatter."""
    missing: list[str] = []
    for agent in sorted(AGENTS_DIR.glob("*.md")):
        keys = _parse_frontmatter_keys(agent)
        for req in ("name", "description"):
            if req not in keys:
                missing.append(f"{agent.name}: '{req}' fehlt")
    assert not missing, "Agent-Frontmatter-Probleme:\n  " + "\n  ".join(missing)


def check_hooks_json_integrity() -> None:
    """hooks/hooks.json: valides JSON + alle referenzierten .mjs-Hooks existieren."""
    hooks_json = HOOKS_DIR / "hooks.json"
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    referenced: set[str] = set()
    for event_list in data.get("hooks", {}).values():
        for entry in event_list:
            for hook in entry.get("hooks", []):
                cmd = hook.get("command", "")
                for m in re.finditer(r"hooks/([A-Za-z0-9._-]+\.mjs)", cmd):
                    referenced.add(m.group(1))
    assert referenced, "Keine .mjs-Hook-Referenzen in hooks.json gefunden"
    missing = [name for name in sorted(referenced) if not (HOOKS_DIR / name).exists()]
    assert not missing, f"hooks.json referenziert fehlende Dateien: {missing}"


def check_tool_three_way_consistency(state: dict[str, Any]) -> None:
    """Drei-Wege-Konsistenz: @mcp.tool (server.py) == README == list_tools."""
    server_tools = TOOL_NAME_RE.findall(SERVER_PY.read_text(encoding="utf-8"))
    assert (
        len(server_tools) == EXPECTED_TOOL_COUNT
    ), f"server.py hat {len(server_tools)} @mcp.tool, erwartet {EXPECTED_TOOL_COUNT}"
    readme = README.read_text(encoding="utf-8")
    not_in_readme = [t for t in server_tools if t not in readme]
    assert not not_in_readme, f"Tools fehlen in README: {not_in_readme}"

    listed = set(state["tool_names"])
    assert set(server_tools) == listed, (
        f"Drift server.py vs list_tools. Nur in server.py: {set(server_tools) - listed}; "
        f"nur in list_tools: {listed - set(server_tools)}"
    )


# ===========================================================================
# D) Scripts
# ===========================================================================


def check_scripts_importable() -> None:
    """Jede scripts/*.py ist importierbar (keine SyntaxError/ImportError).

    Importiert die Scripts in ihrer designierten Umgebung: ``scripts/`` liegt
    vorne im ``sys.path`` (so wie der CLI-Entrypoint und die bestehende Suite,
    z.B. ``test_dedup.py``/``test_search.py``, es tun). Mehrere Scripts nutzen
    bewusst Sibling-Imports wie ``from text_utils import …`` — diese sind nur
    in genau dieser Top-Level-Umgebung auflösbar, NICHT als ``scripts.X``-Paket.
    """
    import importlib

    scripts_path = str(SCRIPTS_DIR)
    inserted = scripts_path not in sys.path
    if inserted:
        sys.path.insert(0, scripts_path)
    try:
        failures: list[str] = []
        for py in sorted(SCRIPTS_DIR.glob("*.py")):
            if py.name == "__init__.py":
                continue
            try:
                importlib.import_module(py.stem)
            except Exception as exc:  # noqa: BLE001 — wir wollen jede Fehlerart sehen
                failures.append(f"{py.name}: {type(exc).__name__}: {exc}")
        assert not failures, "Nicht importierbare Scripts:\n  " + "\n  ".join(failures)
    finally:
        if inserted and scripts_path in sys.path:
            sys.path.remove(scripts_path)


def check_script_pure_function() -> None:
    """Reine Funktion ohne Netzwerk: page_offset._extract_page_number auf Fixtures."""
    scripts_path = str(SCRIPTS_DIR)
    inserted = scripts_path not in sys.path
    if inserted:
        sys.path.insert(0, scripts_path)
    try:
        from page_offset import _extract_page_number
    finally:
        if inserted and scripts_path in sys.path:
            sys.path.remove(scripts_path)

    # Arabische Seitenzahl in erster Zeile -> erkannt.
    assert _extract_page_number("1\nKapitel-Inhalt hier") == 1
    # Arabische Seitenzahl in letzter Zeile -> erkannt.
    assert _extract_page_number("Inhalt\nmehr Text\n42") == 42
    # Römische Ziffern werden ignoriert.
    assert _extract_page_number("vii\nVorwort-Text") is None
    # Kein Seitenzahl-Kandidat -> None.
    assert _extract_page_number("nur Fliesstext ohne Zahl am Rand") is None
    # Leerer Text -> None.
    assert _extract_page_number("") is None


# ===========================================================================
# Registry: kategorisierte Checks (für den Standalone-Reporter)
# ===========================================================================

# Checks, die das geteilte MCP-Round-Trip-State-dict benötigen.
StateCheck = Callable[[dict[str, Any]], None]
# Checks ohne Argument.
PlainCheck = Callable[[], None]


def stateful_checks() -> list[tuple[str, str, StateCheck]]:
    """(Kategorie, Name, Funktion) für alle State-abhängigen Checks."""
    return [
        ("A) MCP-Lifecycle", "list_tools == 33", check_mcp_lifecycle),
        ("A) MCP-Lifecycle", "papers add/get/search/stats", check_mcp_papers),
        ("A) MCP-Lifecycle", "provenance audit", check_mcp_provenance),
        ("A) MCP-Lifecycle", "chapter", check_mcp_chapter),
        ("A) MCP-Lifecycle", "quotes add/search/find/get", check_mcp_quotes),
        ("A) MCP-Lifecycle", "figures add/get/list", check_mcp_figures),
        ("A) MCP-Lifecycle", "page-offset math", check_mcp_page_offset),
        ("A) MCP-Lifecycle", "decisions + supersede", check_mcp_decisions),
        ("A) MCP-Lifecycle", "excluded sources", check_mcp_excluded),
        ("A) MCP-Lifecycle", "risk-of-bias", check_mcp_risk_of_bias),
        ("A) MCP-Lifecycle", "score snapshots/history", check_mcp_scores),
        ("A) MCP-Lifecycle", "material passport + lock", check_mcp_passport),
        ("A) MCP-Lifecycle", "snapshot export/restore", check_mcp_snapshot),
        ("A) MCP-Lifecycle", "NEG malformed csl_json", check_mcp_malformed_csl),
        ("C) Struktur-Gate", "tool 3-way consistency", check_tool_three_way_consistency),
    ]


def plain_checks() -> list[tuple[str, str, PlainCheck]]:
    """(Kategorie, Name, Funktion) für alle State-unabhängigen Checks."""
    return [
        ("B) Hooks", "verbatim-guard allow/block", check_hook_verbatim_guard),
        ("B) Hooks", "decisions-log hash + 0600", check_hook_decisions_log),
        ("B) Hooks", "pre-compact/mid-session no-crash", check_hook_no_crash),
        (
            "C) Struktur-Gate",
            "plugin/marketplace consistency",
            check_plugin_marketplace_consistency,
        ),
        ("C) Struktur-Gate", "skills frontmatter", check_skills_frontmatter),
        ("C) Struktur-Gate", "commands frontmatter", check_commands_frontmatter),
        ("C) Struktur-Gate", "agents frontmatter", check_agents_frontmatter),
        ("C) Struktur-Gate", "hooks.json integrity", check_hooks_json_integrity),
        ("D) Scripts", "all scripts importable", check_scripts_importable),
        ("D) Scripts", "page_offset pure function", check_script_pure_function),
    ]
