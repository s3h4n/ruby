"""Markdown normalization for text-to-speech output."""

from __future__ import annotations

import re


_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_BRACKETED_TEXT_PATTERN = re.compile(r"\[([^\]]+)\]")
_INLINE_CODE_PATTERN = re.compile(r"`([^`]+)`")
_BOLD_ITALIC_PATTERN = re.compile(r"(\*\*|__|\*)([^\n]+?)\1")
_ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)_([^\n]+?)_(?!\w)")
_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+")
_ORDERED_LIST_PATTERN = re.compile(r"^\s*(\d+)\.\s+")
_UNORDERED_LIST_PATTERN = re.compile(r"^\s*[-*+]\s+")
_UNDERSCORE_PATTERN = re.compile(r"(?<=\w)_(?=\w)")
_SNAKE_CALL_PATTERN = re.compile(r"\b([A-Za-z]+(?:_[A-Za-z0-9]+)+)\(\)")
_OPERATOR_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("<->", " then "),
    ("->", " then "),
    ("=>", " then "),
    ("<-", " then "),
)


def markdown_to_speech_text(markdown: str) -> str:
    """Return conservative plain text suitable for TTS synthesis."""
    if not markdown.strip():
        return ""

    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    rendered: list[str] = []
    in_code_fence = False
    table_header: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.strip().startswith("```"):
            in_code_fence = not in_code_fence
            continue

        if in_code_fence:
            if line.strip():
                rendered.append(line.strip())
            continue

        if _looks_like_table_separator(line):
            continue

        if "|" in line and line.count("|") >= 2:
            cells = _extract_table_cells(line)
            if not cells:
                continue
            if not table_header:
                table_header = cells
                continue
            rendered.append(_render_table_row(table_header, cells))
            continue

        table_header = []

        normalized = line.strip()
        if not normalized:
            rendered.append("")
            continue

        normalized = _HEADING_PATTERN.sub("", normalized)
        normalized = _LINK_PATTERN.sub(r"\1", normalized)
        normalized = _INLINE_CODE_PATTERN.sub(r"\1", normalized)
        normalized = _BOLD_ITALIC_PATTERN.sub(r"\2", normalized)
        normalized = _ITALIC_UNDERSCORE_PATTERN.sub(r"\1", normalized)

        if _UNORDERED_LIST_PATTERN.match(normalized):
            normalized = _UNORDERED_LIST_PATTERN.sub("", normalized)
        elif _ORDERED_LIST_PATTERN.match(normalized):
            normalized = _ORDERED_LIST_PATTERN.sub("", normalized)

        rendered.append(normalized)

    compact = "\n".join(rendered)
    compact = re.sub(r"\n{3,}", "\n\n", compact)
    return _normalize_symbols_for_speech(compact)


def _normalize_symbols_for_speech(text: str) -> str:
    normalized = text

    for source, target in _OPERATOR_REPLACEMENTS:
        normalized = normalized.replace(source, target)

    normalized = normalized.replace("+", " plus ")
    normalized = normalized.replace("=", " equals ")
    normalized = normalized.replace("\\", " ")
    normalized = normalized.replace("/", " ")

    normalized = _BRACKETED_TEXT_PATTERN.sub(r"\1", normalized)
    normalized = _SNAKE_CALL_PATTERN.sub(r"\1", normalized)
    normalized = _UNDERSCORE_PATTERN.sub(" ", normalized)

    normalized = re.sub(r"[{}\[\]]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _looks_like_table_separator(line: str) -> bool:
    stripped = line.strip()
    if "|" not in stripped:
        return False
    candidate = stripped.replace("|", "").replace(":", "").replace("-", "")
    return candidate.strip() == ""


def _extract_table_cells(line: str) -> list[str]:
    segments = [segment.strip() for segment in line.split("|")]
    if segments and segments[0] == "":
        segments = segments[1:]
    if segments and segments[-1] == "":
        segments = segments[:-1]
    return [cell for cell in segments if cell]


def _render_table_row(header: list[str], row: list[str]) -> str:
    pairs: list[str] = []
    for index, value in enumerate(row):
        key = header[index] if index < len(header) else f"column {index + 1}"
        pairs.append(f"{key} {value}")
    return "; ".join(pairs)
