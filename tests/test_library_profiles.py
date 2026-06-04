"""Tests fuer Per-Uni-Profile (Chunk B, v6.2 F16.5)."""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml
from jsonschema import ValidationError, validate

# Pfade relativ zum Repo-Root
REPO_ROOT = Path(__file__).parent.parent
PROFILES_DIR = REPO_ROOT / "config" / "library-profiles"
SCHEMA_PATH = PROFILES_DIR / "_schema.json"
PROFILE_SLUGS = ["tum", "fu-berlin", "eth-zurich", "uni-wien", "uni-hamburg"]
HOOK_PATH = REPO_ROOT / "hooks" / "onboard-project-uni-prompt.sh"


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def load_profile(slug: str) -> dict:
    with open(PROFILES_DIR / f"{slug}.yaml") as f:
        return yaml.safe_load(f)


# ── Positiv-Tests ────────────────────────────────────────────────────────────

class TestProfilesValidPositiv:
    """Alle 5 Profile muessen gegen _schema.json valide sein."""

    def test_tum_valid(self):
        validate(instance=load_profile("tum"), schema=load_schema())

    def test_fu_berlin_valid(self):
        validate(instance=load_profile("fu-berlin"), schema=load_schema())

    def test_eth_zurich_valid(self):
        validate(instance=load_profile("eth-zurich"), schema=load_schema())

    def test_uni_wien_valid(self):
        validate(instance=load_profile("uni-wien"), schema=load_schema())

    def test_uni_hamburg_valid(self):
        validate(instance=load_profile("uni-hamburg"), schema=load_schema())


# ── Negativ-Tests ────────────────────────────────────────────────────────────

class TestSchemaValidierungNegativ:
    """Schema muss bei fehlenden/falschen Pflichtfeldern ValidationError werfen."""

    def _base_profile(self) -> dict:
        """Minimales gueltiges Profil als Ausgangsbasis fuer Negativ-Tests."""
        return {
            "uni": "test-uni",
            "auth_type": "Shibboleth",
            "auth_url": "https://shibboleth.example.de",
            "licensed_sites": ["link.springer.com"],
            "bib_pickup_url": "https://opac.example.de",
        }

    def test_fehlendes_bib_pickup_url(self):
        profile = self._base_profile()
        del profile["bib_pickup_url"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlendes_uni(self):
        profile = self._base_profile()
        del profile["uni"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlendes_auth_type(self):
        profile = self._base_profile()
        del profile["auth_type"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_ungültiger_auth_type(self):
        profile = self._base_profile()
        profile["auth_type"] = "LDAP"
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_leere_licensed_sites(self):
        profile = self._base_profile()
        profile["licensed_sites"] = []  # minItems: 1
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlendes_auth_url(self):
        profile = self._base_profile()
        del profile["auth_url"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_fehlende_licensed_sites(self):
        profile = self._base_profile()
        del profile["licensed_sites"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_wildcard_host_abgelehnt(self):
        """Wildcard-Hosts wie *.springer.com sind in licensed_sites verboten."""
        profile = self._base_profile()
        profile["licensed_sites"] = ["*.springer.com"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())

    def test_url_als_host_abgelehnt(self):
        """Vollstaendige URLs wie https://springer.com sind als licensed_sites-Eintraege verboten."""
        profile = self._base_profile()
        profile["licensed_sites"] = ["https://springer.com"]
        with pytest.raises(ValidationError):
            validate(instance=profile, schema=load_schema())


# ── README-Konsistenz-Tests ───────────────────────────────────────────────────

README_PATH = REPO_ROOT / "README.md"


class TestReadmeKonsistenz:
    """README muss den tatsaechlichen Zustand von config/library-profiles/ widerspiegeln."""

    def _readme_text(self) -> str:
        return README_PATH.read_text(encoding="utf-8")

    def test_readme_nennt_korrekten_pfad(self):
        """README darf 'library-profiles/<uni>.yaml' nicht mehr als Pfad nennen (ohne config/ Praefix)."""
        readme = self._readme_text()
        # Suche nach dem Fehlmuster: library-profiles/ ohne config/ davor
        # Erlaube nur 'config/library-profiles/' oder Runtime-Pfad '~/.academic-research/library-profiles/'
        bad_matches = re.findall(
            r"(?<!config/)(?<!academic-research/)library-profiles/[^`\s]*\.yaml",
            readme,
        )
        assert bad_matches == [], (
            f"README enthaelt Pfade ohne 'config/'-Praefix: {bad_matches}. "
            "Korrekt: 'config/library-profiles/<uni>.yaml'."
        )

    def test_readme_listet_tatsaechliche_profile(self):
        """Die Profile die README in der Per-Uni-Profile-Tabelle listet muessen mit den tatsaechlichen Dateien uebereinstimmen."""
        actual_slugs = {
            p.stem for p in PROFILES_DIR.glob("*.yaml")
        }
        # Erwartete tatsaechliche Slugs gemaess Dateisystem
        expected_slugs = set(PROFILE_SLUGS)
        assert actual_slugs == expected_slugs, (
            f"Dateisystem-Profile: {sorted(actual_slugs)}, "
            f"Erwartete Profile gemaess PROFILE_SLUGS: {sorted(expected_slugs)}"
        )

    def test_readme_erwaehnt_keine_nicht_existenten_profile(self):
        """Profil-Dateien die README im Per-Uni-Profile-Abschnitt erwaehnt muessen existieren."""
        readme = self._readme_text()
        # Suche nach dem Abschnitt '## Per-Uni-Profile' und lese die Tabelle
        section_match = re.search(
            r"## Per-Uni-Profile.*?(?=\n## |\Z)", readme, re.DOTALL
        )
        assert section_match, "Abschnitt '## Per-Uni-Profile' nicht im README gefunden"
        section = section_match.group(0)
        # Nur einfache Dateinamen ohne Pfad-Separator und ohne Platzhalter (<>) extrahieren
        # (z.B. 'tum.yaml', 'fu-berlin.yaml' — nicht 'config/library-profiles/<uni>.yaml')
        mentioned_yamls = re.findall(r"`([a-z0-9_-]+\.yaml)`", section)
        # Templates herausfiltern (template-*.yaml sind Vorlagen und existieren ggf. nicht)
        non_template_yamls = [y for y in mentioned_yamls if not y.startswith("template-")]
        missing = [
            y for y in non_template_yamls
            if not (PROFILES_DIR / y).exists()
        ]
        assert missing == [], (
            f"README erwaehnt Profile die nicht in config/library-profiles/ existieren: {missing}"
        )

    def test_readme_per_uni_pfad_ist_config_library_profiles(self):
        """Der Per-Uni-Profile Abschnitt muss 'config/library-profiles/' als Pfad dokumentieren."""
        readme = self._readme_text()
        section_match = re.search(
            r"## Per-Uni-Profile.*?(?=\n## |\Z)", readme, re.DOTALL
        )
        assert section_match, "Abschnitt '## Per-Uni-Profile' nicht im README gefunden"
        section = section_match.group(0)
        assert "config/library-profiles/" in section, (
            "Per-Uni-Profile-Abschnitt muss 'config/library-profiles/' als Pfad enthalten, "
            "nicht 'library-profiles/'"
        )


# ── Onboard-Hook-Tests ───────────────────────────────────────────────────────

class TestOnboardHook:
    """Hook schreibt active.yaml korrekt."""

    def test_hook_file_exists(self):
        assert HOOK_PATH.exists(), f"Hook nicht gefunden: {HOOK_PATH}"

    def test_hook_ist_ausfuehrbar(self):
        assert os.access(HOOK_PATH, os.X_OK), f"Hook nicht ausfuehrbar: {HOOK_PATH}"

    def test_hook_schreibt_active_yaml(self, tmp_path):
        """--profile <slug> Flag schreibt active.yaml in tmp_path."""
        active_dir = tmp_path / "library-profiles"
        active_dir.mkdir()
        active_yaml = active_dir / "active.yaml"

        result = subprocess.run(
            ["bash", str(HOOK_PATH), "--profile", "tum", "--output-dir", str(active_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Hook Fehler: {result.stderr}"
        assert active_yaml.exists(), "active.yaml wurde nicht erstellt"

        with open(active_yaml) as f:
            content = yaml.safe_load(f)
        assert content["uni"] == "tum"
        assert content["auth_type"] == "Shibboleth"

    def test_hook_active_yaml_ist_valide(self, tmp_path):
        """Das von Hook geschriebene active.yaml validiert gegen Schema."""
        active_dir = tmp_path / "library-profiles"
        active_dir.mkdir()

        subprocess.run(
            ["bash", str(HOOK_PATH), "--profile", "tum", "--output-dir", str(active_dir)],
            capture_output=True,
        )

        with open(active_dir / "active.yaml") as f:
            content = yaml.safe_load(f)
        validate(instance=content, schema=load_schema())
