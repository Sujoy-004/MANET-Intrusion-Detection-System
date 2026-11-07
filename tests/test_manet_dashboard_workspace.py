"""Tests for MANET IDS Operational Dashboard workspace composition and widgets.

Verifies:
- End-to-end tracer diagnostic card mounts on MainWorkspace
- Top status cards render real diagnostic data without mock values
- ActiveWorkloadCard distinguishes engine ready (offline) from active running state
- Persistent rails (StatusBar, NotificationRail, NavRail) fulfill D-05 mounting contract
- NavRail displays honest action labels including Console as logs & diagnostics interface
"""

from __future__ import annotations

import platform
import sys
import pytest

from manet.adapters.diagnostics import (
    CapabilityStatus,
    DiagnosticsProbe,
    DiagnosticsReport,
)
from manet.adapters.status import StatusAdapter, WorkloadStatus
from manet.app import ManetApp
from manet.screens.main_workspace import MainWorkspace
from manet.widgets.dashboard_cards import (
    ActiveWorkloadCard,
    ComponentCapabilitiesCard,
    SystemHealthCard,
)
from manet.widgets.nav_rail import NavRail
from manet.widgets.notification_rail import NotificationRail
from manet.widgets.status_bar import StatusBar


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


def test_cards_render():
    """Verify top status cards render accurate runtime data, inline badges, and zero mock values."""
    # 1. SystemHealthCard
    health_card = SystemHealthCard()
    health_text = str(health_card.render())
    expected_py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected_plat = platform.system()
    assert expected_py_ver in health_text
    assert expected_plat in health_text
    assert "System Health" in health_text
    assert "Dependencies:" in health_text

    # 2. ComponentCapabilitiesCard
    cap_card = ComponentCapabilitiesCard()
    cap_text = str(cap_card.render())
    assert "Component Capabilities" in cap_text
    assert "Scenarios:" in cap_text
    assert "Datasets:" in cap_text
    assert "Champion:" in cap_text

    # Test custom report with Grayhole F1 0.0 and unavailable dataset remediation
    custom_report = DiagnosticsReport(
        python_version=(expected_py_ver, True),
        dependencies={"simpy": (True, "4.1.2")},
        scenarios=CapabilityStatus("Scenarios", "VERIFIED", "5 valid presets available"),
        datasets=CapabilityStatus(
            "Datasets",
            "UNAVAILABLE",
            "Missing: data/train.csv, data/test.csv",
            remediation="Run python scripts/build_dataset.py --multi-attack",
        ),
        model_artifact=CapabilityStatus(
            "Champion Model",
            "PARTIAL",
            "Random Forest (BH F1: 0.7593, PARTIAL (Grayhole F1: 0.0 - Ineffective Detection), FPR: 0.0099)",
            remediation="Multi-attack tuning required for Grayhole detection",
        ),
    )
    cap_card.update_report(custom_report)
    updated_cap_text = str(cap_card.render())
    assert "PARTIAL (Grayhole F1: 0.0 - Ineffective Detection)" in updated_cap_text
    assert "UNAVAILABLE" in updated_cap_text
    assert "Run python scripts/build_dataset.py --multi-attack" in updated_cap_text
    assert "Multi-attack tuning required for Grayhole detection" in updated_cap_text

    # 3. ActiveWorkloadCard
    workload_card = ActiveWorkloadCard()
    workload_text = str(workload_card.render())
    assert "Active Workload" in workload_text
    assert "IDLE" in workload_text
    assert "No active simulation" in workload_text
    assert "AODV Engine Ready (Offline)" in workload_text
    assert "AODV Active" not in workload_text, "Idle state must not claim AODV is actively running"

    # Verify custom workload status updates correctly
    running_status = WorkloadStatus(
        workload_state="RUNNING",
        engine_state="AODV Engine In-Flight",
        description="Scenario: 50-node random waypoint",
    )
    workload_card.update_status(running_status)
    running_text = str(workload_card.render())
    assert "RUNNING" in running_text
    assert "AODV Engine In-Flight" in running_text
    assert "Scenario: 50-node random waypoint" in running_text


def test_rails_render():
    """Verify persistent rails (NavRail, NotificationRail, StatusBar) display honest content."""
    # 1. NavRail
    nav_rail = NavRail()
    nav_text = str(nav_rail.render())
    assert "Quick Navigation" in nav_text
    assert "[S]" in nav_text and "Simulation (Phase 9 Notice)" in nav_text
    assert "[R]" in nav_text and "Results (Phase 11 Notice)" in nav_text
    assert "[CTRL+O]" in nav_text and "Console (Logs & Diagnostics)" in nav_text
    assert "[CTRL+P]" in nav_text and "Palette" in nav_text
    assert "[F1]" in nav_text and "Help" in nav_text

    # 2. NotificationRail
    notif_rail = NotificationRail()
    assert notif_rail.get_active_notice() is None
    assert str(notif_rail.render()) == ""
    assert notif_rail.display is False

    notif_rail.notify_user("Simulation workflow pending in Phase 9", level="info")
    assert notif_rail.get_active_notice() == "Simulation workflow pending in Phase 9"
    notif_text = str(notif_rail.render())
    assert "Simulation workflow pending in Phase 9" in notif_text
    assert notif_rail.display is True

    notif_rail.dismiss()
    assert notif_rail.get_active_notice() is None
    assert str(notif_rail.render()) == ""
    assert notif_rail.display is False

    # 3. StatusBar
    status_bar = StatusBar()
    status_text = str(status_bar.render())
    assert "System Ready" in status_text
    assert "Workspace:" in status_text
    assert "Engine:" in status_text
    assert "Press" in status_text and "F1" in status_text
