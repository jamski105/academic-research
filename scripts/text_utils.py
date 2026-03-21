#!/usr/bin/env python3
"""Shared utilities for academic-research v4 scripts."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Paper:
    """Normalized paper schema used across all modules."""

    doi: str | None = None
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    abstract: str | None = None
    venue: str | None = None
    citations: int = 0
    url: str | None = None
    source_module: str = ""
    oa_url: str | None = None
    open_access_pdf: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Paper:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def normalize_paper(data: dict[str, Any], source_module: str) -> dict[str, Any]:
    """Normalize source-specific payload to common paper schema dict."""
    return {
        "doi": data.get("doi"),
        "title": data.get("title"),
        "authors": data.get("authors") or [],
        "year": data.get("year"),
        "abstract": data.get("abstract"),
        "venue": data.get("venue"),
        "citations": int(data.get("citations") or 0),
        "url": data.get("url"),
        "source_module": source_module,
        "oa_url": data.get("oa_url"),
        "open_access_pdf": data.get("open_access_pdf"),
    }


def normalize_doi(doi: str | None) -> str | None:
    """Normalize DOI to lowercase without URL prefix."""
    if not doi:
        return None
    value = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value or None


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric terms."""
    return [t for t in re.split(r"[^a-z0-9äöüß]+", text.lower()) if t]


def safe_filename(text: str, max_length: int = 80) -> str:
    """Create a filesystem-safe filename from text."""
    clean = re.sub(r"[^\w\s-]", "", text.lower())
    clean = re.sub(r"[\s_]+", "_", clean).strip("_")
    return clean[:max_length]


def load_json(path: str | Path) -> Any:
    """Load JSON from file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Save data as JSON to file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent)


def load_yaml(path: str | Path) -> Any:
    """Load YAML from file."""
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
