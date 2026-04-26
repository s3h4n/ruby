"""Model and binary discovery helpers for init and diagnostics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


def discover_whisper_binaries(candidates: Iterable[Path]) -> list[Path]:
    discovered: list[Path] = []
    for candidate in candidates:
        path = candidate.expanduser().resolve()
        if path.exists() and path.is_file():
            discovered.append(path)
    deduped = sorted(set(discovered), key=str)
    return deduped


def discover_whisper_models(search_dirs: Iterable[Path]) -> list[Path]:
    matches: list[Path] = []
    for directory in search_dirs:
        path = directory.expanduser().resolve()
        if not path.exists() or not path.is_dir():
            continue
        matches.extend(path.glob("ggml-*.bin"))
    return sorted(set(item.resolve() for item in matches), key=str)


def ollama_tags_url(chat_url: str) -> str:
    parsed = urlparse(chat_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return f"{base}/api/tags"


def discover_ollama_models(chat_url: str, timeout_seconds: int = 5) -> tuple[bool, list[str], str]:
    try:
        import requests
    except ModuleNotFoundError:
        return False, [], "Missing dependency 'requests'. Install requirements first."

    tags_url = ollama_tags_url(chat_url)
    try:
        response = requests.get(tags_url, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exc:
        return False, [], f"Could not reach Ollama tags API at {tags_url}: {exc}"

    payload = response.json()
    model_entries = payload.get("models", [])
    names: list[str] = []
    for item in model_entries:
        name = str(item.get("name", "")).strip()
        if name:
            names.append(name)
    return True, sorted(set(names)), "OK"


def is_safe_ollama_model_name(model_name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._:/-]+", model_name.strip()))
