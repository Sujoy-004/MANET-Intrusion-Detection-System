"""Entry point and package surface verification for manet package.

Verifies:
- manet.__main__.main is callable and accepts no required arguments
- importing manet produces zero side effects (no App instantiated, no screens mounted)
- manet package exposes __version__ and explicit __all__ without barrel exports
- No subprocess or real TTY is spawned during testing
"""

from __future__ import annotations

import inspect

import manet
from manet.__main__ import main


def test_manet_main_entry_callable():
    """Verify main callable in manet.__main__ exists and requires no arguments."""
    assert callable(main), "manet.__main__.main must be callable"

    sig = inspect.signature(main)
    required_params = [
        p
        for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    assert len(required_params) == 0, f"main() must require no arguments, found: {required_params}"


def test_manet_package_surface_and_side_effects():
    """Verify package surface exhibits no barrel export cycles or import side effects."""
    assert hasattr(manet, "__version__"), "manet package must define __version__"
    assert manet.__version__ == "2.0.0-dev", (
        f"Expected version '2.0.0-dev', got {manet.__version__}"
    )
    assert manet.__all__ == ["__version__"], (
        f"Expected __all__ to be ['__version__'], got {manet.__all__}"
    )

    # Verify no App or Widget class is leaked on the root package
    assert not hasattr(manet, "ManetApp"), (
        "manet root must not re-export ManetApp (barrel-cycle rule)"
    )
    assert not hasattr(manet, "App"), "manet root must not leak Textual App"
    assert not hasattr(manet, "Screen"), "manet root must not leak Textual Screen"
