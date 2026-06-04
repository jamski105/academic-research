"""
Regressionstest fuer Issue #238.

commands/search.md listete `quote-extractor` in `allowed-tools` (Agent(...)),
rief den Agenten aber nirgends im Workflow-Body auf. Dieser Test sichert die
Konsistenz zwischen den in `allowed-tools` deklarierten Agenten und den
tatsaechlich im Command-Body referenzierten Agenten ab.

Akzeptanzkriterium (Issue #238):
- `allowed-tools` spiegelt die tatsaechlich genutzten Agenten wider.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SEARCH_COMMAND = REPO_ROOT / "commands/search.md"


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Trennt YAML-Frontmatter vom Markdown-Body."""
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "Frontmatter-Start '---' fehlt"
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    assert end is not None, "Frontmatter-Ende '---' fehlt"
    frontmatter = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :])
    return frontmatter, body


def _allowed_tools_line(frontmatter: str) -> str:
    for line in frontmatter.splitlines():
        if line.strip().startswith("allowed-tools:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("Kein 'allowed-tools:' in Frontmatter gefunden")


def _agents_in_allowed_tools(allowed_tools: str) -> list[str]:
    """Extrahiert Agent-Namen aus 'Agent(a, b, c)' der allowed-tools-Zeile."""
    m = re.search(r"Agent\(([^)]*)\)", allowed_tools)
    if not m:
        return []
    return [a.strip() for a in m.group(1).split(",") if a.strip()]


def test_frontmatter_description_non_empty():
    """CI-Gate: description muss nicht-leer bleiben."""
    frontmatter, _ = _split_frontmatter(SEARCH_COMMAND.read_text(encoding="utf-8"))
    desc = None
    for line in frontmatter.splitlines():
        if line.strip().startswith("description:"):
            desc = line.split(":", 1)[1].strip()
            break
    assert desc, "description: muss vorhanden und nicht-leer sein"


def test_every_allowed_agent_is_invoked_in_body():
    """Jeder in allowed-tools deklarierte Agent muss im Body referenziert werden."""
    text = SEARCH_COMMAND.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    agents = _agents_in_allowed_tools(_allowed_tools_line(frontmatter))

    assert agents, "Erwartet mindestens einen Agenten in allowed-tools"

    orphaned = [a for a in agents if a not in body]
    assert not orphaned, (
        f"Agenten in allowed-tools, aber nie im Body aufgerufen: {orphaned}. "
        "allowed-tools muss die tatsaechlich genutzten Agenten widerspiegeln (Issue #238)."
    )


def test_quote_extractor_not_in_allowed_tools():
    """quote-extractor wird im Search-Workflow nicht genutzt -> darf nicht deklariert sein."""
    text = SEARCH_COMMAND.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    agents = _agents_in_allowed_tools(_allowed_tools_line(frontmatter))

    assert "quote-extractor" not in agents, (
        "quote-extractor steht in allowed-tools, wird aber im Search-Workflow "
        "nirgends aufgerufen (Issue #238)."
    )
    # Gegenprobe: quote-extractor kommt auch sonst nicht im Body vor.
    assert "quote-extractor" not in body, (
        "quote-extractor sollte nach der Bereinigung gar nicht mehr in search.md stehen."
    )


def test_actually_used_agents_remain_declared():
    """Die genutzten Agenten (query-generator, relevance-scorer) bleiben deklariert."""
    text = SEARCH_COMMAND.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    agents = _agents_in_allowed_tools(_allowed_tools_line(frontmatter))

    for used in ("query-generator", "relevance-scorer"):
        assert used in body, f"{used} sollte im Body genutzt werden (Sanity-Check)"
        assert used in agents, f"{used} muss in allowed-tools deklariert bleiben"
