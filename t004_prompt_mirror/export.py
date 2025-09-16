"""Utility helpers for exporting rewritten prompts."""
from __future__ import annotations


def to_txt(rewrite: str) -> bytes:
    """Return the rewritten prompt as UTF-8 encoded bytes for download."""
    content = rewrite or ""
    return content.encode("utf-8")
