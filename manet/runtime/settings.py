"""In-memory session settings for MANET IDS TUI.

Provides the SessionSettings dataclass governing runtime accessibility, visual contrast,
and display density toggles.

Architectural Constraint (D-09):
All settings stored in this module are strictly session-only and in-memory.
No configuration profiles, preferences, or cached state are ever persisted to disk.
This module strictly avoids file writes, serializations, or external preference storage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SessionSettings:
    """Session-only settings managing in-memory user preferences.

    Attributes:
        high_contrast: Whether high-contrast visual theme is active.
        reduced_motion: Whether animations and visual motion effects are suppressed.
        compact_density: Whether compact layout density mode is enforced.
    """

    high_contrast: bool = False
    reduced_motion: bool = False
    compact_density: bool = False

    @property
    def compact_mode(self) -> bool:
        """Alias for compact_density to support alternative naming conventions."""
        return self.compact_density

    @compact_mode.setter
    def compact_mode(self, value: bool) -> None:
        self.compact_density = value


__all__ = ["SessionSettings"]
