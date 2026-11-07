"""Tests for MANET IDS Operational Dashboard workspace composition and widgets.

Verifies:
- End-to-end tracer diagnostic card mounts on MainWorkspace
- SystemHealthCard displays real Python runtime version without mock values
"""

from __future__ import annotations

import sys
import pytest

from manet.app import ManetApp
from manet.screens.main_workspace import MainWorkspace
from manet.widgets.dashboard_cards import SystemHealthCard


@pytest.mark.asyncio
async def test_tracer_diagnostic_card_mount():
    """Verify SystemHealthCard is mounted on MainWorkspace and displays real runtime Python version."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)
        card = app.screen.query_one("#card-health", SystemHealthCard)
        assert card.is_mounted

        expected_py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        rendered_text = str(card.render())
        assert expected_py_ver in rendered_text, (
            f"Expected Python version '{expected_py_ver}' in SystemHealthCard output, got: {rendered_text}"
        )
