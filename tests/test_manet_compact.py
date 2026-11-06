"""Tests for responsive terminal breakpoints and compact mode in MANET IDS TUI.

Verifies:
- MainWorkspace declares HORIZONTAL_BREAKPOINTS for adaptive layout sizing (D-18, TUI-02).
- When launched or resized to compact dimensions (60x20), the '-compact' class engages.
- Header and Footer remain mounted and visible without collisions under compact mode.
- When launched at normal/wide dimensions (120x40), the '-normal' class engages.
"""

from __future__ import annotations

import pytest
from textual.widgets import Footer, Header, Static

from manet.app import ManetApp
from manet.screens.main_workspace import MainWorkspace


@pytest.mark.asyncio
async def test_compact_breakpoint_engagement_small_terminal():
    """Verify '-compact' class activates at terminal width < 80 and core widgets mount."""
    app = ManetApp()
    async with app.run_test(size=(60, 20)) as pilot:
        assert isinstance(app.screen, MainWorkspace)
        assert app.screen.has_class("-compact"), (
            f"Expected '-compact' class at width 60, but screen classes are: {app.screen.classes}"
        )
        assert not app.screen.has_class("-normal")

        # Verify Header and Footer mount and remain in composition
        header = app.screen.query_one(Header)
        footer = app.screen.query_one(Footer)
        box = app.screen.query_one("#workspace-box", Static)

        assert header.is_mounted
        assert footer.is_mounted
        assert box.is_mounted
        assert header.display is True
        assert footer.display is True


@pytest.mark.asyncio
async def test_normal_breakpoint_engagement_large_terminal():
    """Verify '-normal' class activates at terminal width >= 80."""
    app = ManetApp()
    async with app.run_test(size=(120, 40)) as pilot:
        assert isinstance(app.screen, MainWorkspace)
        assert app.screen.has_class("-normal"), (
            f"Expected '-normal' class at width 120, but screen classes are: {app.screen.classes}"
        )
        assert not app.screen.has_class("-compact")


def test_main_workspace_declares_horizontal_breakpoints():
    """Verify MainWorkspace class statically declares expected breakpoint thresholds."""
    assert hasattr(MainWorkspace, "HORIZONTAL_BREAKPOINTS"), (
        "MainWorkspace missing HORIZONTAL_BREAKPOINTS class attribute"
    )
    expected = [(0, "-compact"), (80, "-normal")]
    assert list(MainWorkspace.HORIZONTAL_BREAKPOINTS) == expected
