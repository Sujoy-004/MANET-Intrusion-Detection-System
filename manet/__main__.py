"""CLI entry point for the MANET IDS terminal user interface application.

Launches the full-screen Textual application with no mandatory flags and offline execution.
"""

from __future__ import annotations

import sys

from manet.app import ManetApp


def main() -> None:
    """Launch the MANET IDS terminal application with composition root injection."""
    try:
        from bootstrap import create_app  # type: ignore[import-not-found]
        app = create_app()
    except (ImportError, ModuleNotFoundError) as err:
        sys.stderr.write(
            f"WARNING: bootstrap.py composition root failed to load ({err}). "
            "Running with offline fallback (executor=None).\n"
        )
        app = ManetApp(executor=None)
    app.run()


if __name__ == "__main__":
    main()
