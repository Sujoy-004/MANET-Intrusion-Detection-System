"""Global pytest configuration: hermetic workspace isolation for all tests.

Per D-01 (Phase 12): test runs must never touch the real ``.manet-workspace/``
directory. Leftover experiment state from manual testing previously leaked
into ``tests/test_manet_dashboard_workspace.py`` assertions and caused flaky
failures depending on disk state.

The autouse fixture below patches ``WorkspaceAdapter.__init__`` so that the
default workspace root (``workspace_root=None``) resolves to a clean,
isolated directory inside pytest's ``tmp_path`` instead of
``<repo>/.manet-workspace``. Tests that pass an explicit ``workspace_root``
are unaffected, and no business logic is modified.

Tests that specifically assert the REAL default root anchoring opt out with
the ``real_workspace_defaults`` marker (used by
``tests/test_manet_paths.py::test_repo_root_anchoring_outside_cwd``).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from manet.adapters.workspace import WorkspaceAdapter


def pytest_configure(config: pytest.Config) -> None:
    """Register the opt-out marker so it is documented and lint-clean."""
    config.addinivalue_line(
        "markers",
        "real_workspace_defaults: opt out of hermetic workspace isolation "
        "(test asserts the real default .manet-workspace anchoring)",
    )


@pytest.fixture(autouse=True)
def isolate_manet_workspace(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[None]:
    """Redirect the default WorkspaceAdapter root into ``tmp_path``.

    Wraps ``WorkspaceAdapter.__init__`` so that ``workspace_root=None``
    resolves to ``tmp_path / "isolated_workspace"``. Explicit
    ``workspace_root`` arguments pass through unchanged. Tests marked with
    ``real_workspace_defaults`` are skipped (they assert the real default).
    """
    if request.node.get_closest_marker("real_workspace_defaults"):
        yield
        return

    original_init = WorkspaceAdapter.__init__

    def isolated_init(self: WorkspaceAdapter, workspace_root: Path | str | None = None) -> None:
        if workspace_root is None:
            workspace_root = tmp_path / "isolated_workspace"
        original_init(self, workspace_root)

    monkeypatch.setattr(WorkspaceAdapter, "__init__", isolated_init)
    yield
