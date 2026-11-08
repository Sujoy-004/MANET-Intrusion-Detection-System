"""Runtime path resolution anchoring default directories to repository root."""

from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    """Return the repository root directory as an absolute resolved Path."""
    return Path(__file__).resolve().parents[2]


__all__ = ["get_project_root"]
