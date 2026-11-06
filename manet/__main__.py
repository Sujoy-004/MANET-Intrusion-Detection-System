"""CLI entry point for the MANET IDS terminal user interface application.

Launches the full-screen Textual application with no mandatory flags and offline execution.
"""

from __future__ import annotations

from manet.app import ManetApp


def main() -> None:
    """Launch the MANET IDS terminal application."""
    ManetApp().run()


if __name__ == "__main__":
    main()
