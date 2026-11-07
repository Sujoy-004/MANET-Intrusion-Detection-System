"""Tests for MANET IDS Operational Dashboard workspace composition and widgets.

Verifies:
- End-to-end tracer diagnostic card mounts on MainWorkspace
- Top status cards render real diagnostic data without mock values
- ActiveWorkloadCard distinguishes engine ready (offline) from active running state
- Persistent rails (StatusBar, NotificationRail, NavRail) fulfill D-05 mounting contract
- NavRail displays honest action labels including Console as logs & diagnostics interface
- CtaHeroPanel renders honest empty-state guidance without false simulation launch claims
- RecentExperimentsTable populates columns and rows accurately in a read-only manner
"""

from __future__ import annotations

import platform
import sys
import pytest

from textual.app import App, ComposeResult

from manet.adapters.diagnostics import (
    CapabilityStatus,
    DiagnosticsProbe,
    DiagnosticsReport,
)
from manet.adapters.status import StatusAdapter, WorkloadStatus
from manet.adapters.workspace import ExperimentSummary, WorkspaceAdapter
from manet.app import ManetApp
from manet.screens.main_workspace import MainWorkspace
from manet.widgets.cta_hero import CtaHeroPanel
from manet.widgets.dashboard_cards import (
    ActiveWorkloadCard,
    ComponentCapabilitiesCard,
    SystemHealthCard,
)
from manet.widgets.nav_rail import NavRail
from manet.widgets.notification_rail import NotificationRail
from manet.widgets.recent_experiments import RecentExperimentsTable
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


def test_cta_hero_render():
    """Verify CtaHeroPanel displays honest pending workflow guidance without false launch claims."""
    cta = CtaHeroPanel()
    rendered = str(cta.render())
    assert "Guided First-Run" in rendered
    assert "Workflow Pending (Phase 9)" in rendered
    assert "[S]" in rendered and "workflow preview notice" in rendered
    assert "scenarios/" in rendered
    assert "data/" in rendered and "ml/models/" in rendered
    assert "Phase 9 (TUI-09)" in rendered
    assert "launch" not in rendered.lower() or "preview notice" in rendered


@pytest.mark.asyncio
async def test_recent_experiments_table():
    """Verify RecentExperimentsTable mounts, adds columns, and populates rows read-only."""
    sample_runs = [
        ExperimentSummary(
            experiment_id="exp-001",
            scenario_name="50-node-blackhole",
            seed=42,
            status="COMPLETED",
            created_at="2026-11-07 10:00:00",
            pdr=0.8752,
        ),
        ExperimentSummary(
            experiment_id="exp-002",
            scenario_name="30-node-baseline",
            seed=101,
            status="COMPLETED",
            created_at="2026-11-07 11:30:00",
            pdr=0.9810,
        ),
    ]

    class TableHostApp(App[None]):
        def compose(self) -> ComposeResult:
            yield RecentExperimentsTable(experiments=sample_runs, id="test-table")

    app = TableHostApp()
    async with app.run_test() as pilot:
        table = app.query_one("#test-table", RecentExperimentsTable)
        assert table.row_count == 2
        # Verify columns exist
        col_labels = [str(col.label) for col in table.columns.values()]
        assert "Run ID" in col_labels
        assert "Scenario" in col_labels
        assert "Seed" in col_labels
        assert "Status" in col_labels
        assert "PDR" in col_labels
        assert "Date" in col_labels

        # Verify row values
        row0 = table.get_row_at(0)
        assert row0[0] == "exp-001"
        assert row0[1] == "50-node-blackhole"
        assert row0[2] == "42"
        assert row0[3] == "COMPLETED"
        assert row0[4] == "0.8752"
        assert row0[5] == "2026-11-07 10:00:00"

        # Verify dynamic repopulation
        table.populate_experiments([
            ExperimentSummary(
                experiment_id="exp-003",
                scenario_name="40-node-grayhole",
                seed=7,
                status="COMPLETED",
                created_at="2026-11-07 12:00:00",
                pdr=None,
            )
        ])
        assert table.row_count == 1
        row_new = table.get_row_at(0)
        assert row_new[0] == "exp-003"
        assert row_new[4] == "N/A"
