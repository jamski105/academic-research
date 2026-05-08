# tests/_capture_skill_sizes.py
# Aufruf: python tests/_capture_skill_sizes.py (aus Plugin-Root)
# Erzeugt tests/baselines/skill_sizes.json mit len(SKILL.md text) pro Skill.
# MUSS VOR jeder SKILL.md-Modifikation ausgefuehrt werden.
import json
from pathlib import Path

SKILLS_DIR = Path("skills")
VENDORED = {"xlsx", "_common"}
data = {}
for p in sorted(SKILLS_DIR.glob("*/SKILL.md")):
    if p.parent.name not in VENDORED:
        data[p.parent.name] = len(p.read_text())

out = Path("tests/baselines/skill_sizes.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
print(f"Baseline captured: {out}")
