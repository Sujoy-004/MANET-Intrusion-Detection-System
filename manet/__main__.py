"""CLI entry point for the MANET IDS terminal user interface application.

Launches the full-screen Textual application with no mandatory flags and offline execution.
"""

from __future__ import annotations

import sys


def main() -> None:
    """Launch the MANET IDS terminal application with composition root injection."""
    try:
        from bootstrap import create_app  # type: ignore[import-not-found]
        app = create_app()
    except (ImportError, ModuleNotFoundError) as err:
        sys.stderr.write(
            f"ERROR: Failed to load bootstrap composition root ({err}).\n"
            "Execution engine unavailable. Ensure bootstrap.py is present at the repository root.\n"
        )
        sys.exit(1)
    app.run()


if __name__ == "__main__":
    main()
