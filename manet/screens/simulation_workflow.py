"""Simulation workflow guided wizard screen managing 3-step configuration and launch allocation."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Footer, Header

from manet.adapters.handoff import SimulationLaunchRequest
from manet.adapters.scenario import ScenarioAdapter
from manet.adapters.workspace import WorkspaceAdapter
from manet.runtime.paths import get_project_root
from manet.widgets.wizard_step_mode import StepModeSelectWidget
from manet.widgets.wizard_step_params import StepParamsWidget
from manet.widgets.wizard_step_review import StepReviewWidget


class SimulationWorkflowScreen(Screen):
    """Multi-step guided wizard screen for MANET simulation workflow.

    Coordinates:
    - Step 1: Scenario & Mode Selection (Preset vs Custom)
    - Step 2: Parameter Configuration with progressive disclosure
    - Step 3: Pre-Flight Review, IDS gating, and collision-free workspace allocation
    """

    HORIZONTAL_BREAKPOINTS = [(0, "-compact"), (80, "-normal")]

    BINDINGS = [
        Binding("escape", "cancel_or_back", "Back / Cancel", show=True),
        Binding("enter", "next_or_launch", "Next / Confirm", show=True),
    ]

    CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    SimulationWorkflowScreen {
        layout: vertical;
        background: $background;
        padding: 0;
    }

    #wizard-switcher {
        height: 1fr;
        background: $surface;
    }

    Screen.-compact #wizard-switcher {
        padding: 0;
    }

    Screen.-normal #wizard-switcher {
        padding: 0 1;
    }
    """

    def __init__(
        self,
        *args: Any,
        scenario_adapter: ScenarioAdapter | None = None,
        workspace_adapter: WorkspaceAdapter | None = None,
        model_path: Path | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.scenario_adapter = scenario_adapter or ScenarioAdapter()
        self.workspace_adapter = workspace_adapter or WorkspaceAdapter()
        self.model_path = model_path or (get_project_root() / "ml" / "models" / "best_model.joblib")
        self.launch_request: SimulationLaunchRequest | None = None
        self.last_completed_launch_request: SimulationLaunchRequest | None = None

    def on_screen_resume(self) -> None:
        """Reset visible wizard state to Step 1 on screen re-entry if a run was confirmed."""
        try:
            switcher = self.query_one("#wizard-switcher", ContentSwitcher)
            if switcher.current == "step-preflight-review" or self.last_completed_launch_request is not None:
                self.reset_workflow(clear_handoff=False)
        except Exception:
            pass

    def reset_workflow(self, clear_handoff: bool = False) -> None:
        """Reset wizard to Step 1 mode selection, defusing stale review confirmations."""
        try:
            switcher = self.query_one("#wizard-switcher", ContentSwitcher)
            switcher.current = "step-mode-select"
            review_widget = self.query_one("#step-preflight-review", StepReviewWidget)
            review_widget.reset_review()
            if clear_handoff:
                self.launch_request = None
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Compose the 3-step wizard hierarchy with ContentSwitcher."""
        yield Header()
        with ContentSwitcher(initial="step-mode-select", id="wizard-switcher"):
            yield StepModeSelectWidget(
                scenario_adapter=self.scenario_adapter,
                id="step-mode-select",
            )
            yield StepParamsWidget(id="step-param-config")
            yield StepReviewWidget(
                model_path=self.model_path,
                workspace_root=self.workspace_adapter.workspace_root,
                id="step-preflight-review",
            )
        yield Footer()

    def action_cancel_or_back(self) -> None:
        """Handle Escape key: go back to previous step, or return to workspace from Step 1."""
        switcher = self.query_one("#wizard-switcher", ContentSwitcher)
        if switcher.current == "step-mode-select":
            if self.app.is_screen_installed("workspace"):
                self.app.switch_screen("workspace")
        elif switcher.current == "step-param-config":
            switcher.current = "step-mode-select"
        elif switcher.current == "step-preflight-review":
            switcher.current = "step-param-config"

    def action_next_or_launch(self) -> None:
        """Handle Enter key: submit current step or confirm launch."""
        switcher = self.query_one("#wizard-switcher", ContentSwitcher)
        if switcher.current == "step-mode-select":
            self.query_one("#step-mode-select", StepModeSelectWidget).action_submit_mode()
        elif switcher.current == "step-param-config":
            self.query_one("#step-param-config", StepParamsWidget).action_submit_parameters()
        elif switcher.current == "step-preflight-review":
            self.query_one("#step-preflight-review", StepReviewWidget).action_confirm_launch()

    def on_step_mode_select_widget_mode_selected(self, event: StepModeSelectWidget.ModeSelected) -> None:
        """Advance to Step 2 with either loaded preset or custom defaults."""
        params_widget = self.query_one("#step-param-config", StepParamsWidget)
        if event.mode == "preset" and event.preset is not None:
            params_widget.load_preset(event.preset)
        else:
            params_widget.set_custom_defaults()

        switcher = self.query_one("#wizard-switcher", ContentSwitcher)
        switcher.current = "step-param-config"

    def on_step_params_widget_parameters_submitted(self, event: StepParamsWidget.ParametersSubmitted) -> None:
        """Advance to Step 3 pre-flight review with validated parameters."""
        review_widget = self.query_one("#step-preflight-review", StepReviewWidget)
        review_widget.update_review(
            config=event.config,
            run_tag=event.run_tag,
            scenario_name=event.scenario_name,
            mode=event.mode,
            model_path=self.model_path,
        )

        switcher = self.query_one("#wizard-switcher", ContentSwitcher)
        switcher.current = "step-preflight-review"

    def on_step_params_widget_parameters_back(self, event: StepParamsWidget.ParametersBack) -> None:
        """Return to Step 1 mode selection."""
        switcher = self.query_one("#wizard-switcher", ContentSwitcher)
        switcher.current = "step-mode-select"

    def on_step_review_widget_review_back(self, event: StepReviewWidget.ReviewBack) -> None:
        """Return to Step 2 parameter configuration."""
        switcher = self.query_one("#wizard-switcher", ContentSwitcher)
        switcher.current = "step-param-config"

    def on_step_review_widget_review_confirmed(self, event: StepReviewWidget.ReviewConfirmed) -> None:
        """Confirm launch, allocate workspace directory, write manifest, and create handoff request."""
        allocated_dir: Path | None = None
        try:
            # 1. Allocate experiment directory
            exp_id, exp_dir = self.workspace_adapter.allocate_experiment_directory(
                scenario_name=event.scenario_name,
                seed=event.seed,
                tag=event.run_tag,
            )
            allocated_dir = exp_dir

            # 2. Write initial launch manifest
            self.workspace_adapter.record_launch_manifest(
                experiment_dir=exp_dir,
                experiment_id=exp_id,
                scenario_name=event.scenario_name,
                seed=event.seed,
                config=event.config,
            )
        except (OSError, ValueError) as exc:
            cleanup_warning = ""
            if allocated_dir is not None and allocated_dir.is_dir():
                try:
                    root_resolved = self.workspace_adapter.workspace_root.resolve()
                    if allocated_dir.resolve().is_relative_to(root_resolved):
                        for item in allocated_dir.iterdir():
                            try:
                                item.unlink()
                            except OSError:
                                pass
                        allocated_dir.rmdir()
                except OSError as clean_err:
                    cleanup_warning = f" (Cleanup warning: {clean_err})"

            review_widget = self.query_one("#step-preflight-review", StepReviewWidget)
            review_widget.show_error(f"Workspace allocation failed: {exc}{cleanup_warning}")
            return

        # 3. Create handoff SimulationLaunchRequest
        ids_cfg = event.config.get("ids", {})
        ids_enabled = bool(ids_cfg.get("enabled", False)) if isinstance(ids_cfg, dict) else False
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        launch_req = SimulationLaunchRequest(
            experiment_id=exp_id,
            scenario_name=event.scenario_name,
            seed=event.seed,
            config=event.config,
            workspace_dir=exp_dir,
            created_at=now_iso,
            ids_enabled=ids_enabled,
        )
        self.launch_request = launch_req
        self.last_completed_launch_request = launch_req
        setattr(self.app, "last_launch_request", launch_req)

        # 4. Defuse stale Step 3 review state and reset wizard to Step 1
        self.reset_workflow(clear_handoff=False)

        # 5. Transition back to workspace and notify
        if self.app.is_screen_installed("workspace"):
            self.app.switch_screen("workspace")
            try:
                workspace_screen = self.app.get_screen("workspace")
                rail = workspace_screen.query_one("#notification-rail")
                rail.notify_user(f"Allocated simulation run {exp_id} in .manet-workspace/ (CONFIGURED)")
            except Exception:
                pass


__all__ = ["SimulationWorkflowScreen"]
