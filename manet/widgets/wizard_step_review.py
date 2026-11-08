"""Step 3: Pre-flight review and launch confirmation widget."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Static

from manet.adapters.simulation_config import validate_structural_invariants
from manet.adapters.workspace import sanitize_run_tag
from manet.runtime.paths import get_project_root


class StepReviewWidget(VerticalScroll):
    """Step 3: Pre-Flight Review & Confirmation.

    Displays consolidated summary of all parameters, estimated scale, champion model status,
    collision-free target workspace directory preview, and enforces IDS gating.
    """

    class ReviewBack(Message):
        """Emitted when user requests returning to Step 2."""

        pass

    class ReviewConfirmed(Message):
        """Emitted when user confirms review and requests allocating run."""

        def __init__(
            self,
            config: dict[str, Any],
            run_tag: str,
            scenario_name: str,
            seed: int,
            mode: str,
        ) -> None:
            super().__init__()
            self.config = config
            self.run_tag = run_tag
            self.scenario_name = scenario_name
            self.seed = seed
            self.mode = mode

    DEFAULT_CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    StepReviewWidget {
        height: 1fr;
        padding: 1 2;
        background: $surface;
    }

    #review-header {
        margin-bottom: 1;
    }

    #review-summary-card {
        background: $panel;
        border: solid $info-blue;
        padding: 1;
        margin-bottom: 1;
    }

    .review-section-title {
        color: $navigation-cyan;
        text-style: bold;
        margin-bottom: 1;
    }

    #review-model-status-box {
        margin-top: 1;
        margin-bottom: 1;
        padding: 1;
        border: solid $warning;
        background: $surface;
    }

    #review-model-status-box.model-ok {
        border: solid $success;
        color: $success;
    }

    #review-model-status-box.model-missing {
        border: solid $error;
        color: $error;
    }

    #review-workspace-box {
        margin-top: 1;
        margin-bottom: 1;
        padding: 1;
        border: solid $info-blue;
        background: $panel;
    }

    #review-errors-display {
        color: $error;
        margin-top: 1;
        margin-bottom: 1;
    }

    #review-actions {
        layout: horizontal;
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    #btn-review-back {
        margin-right: 2;
        min-width: 14;
    }

    #btn-review-launch {
        min-width: 28;
    }
    """

    def __init__(
        self,
        *args,
        model_path: Path | None = None,
        workspace_root: Path | None = None,
        id: str | None = "step-preflight-review",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, id=id, classes=classes, **kwargs)
        self.model_path = model_path or (get_project_root() / "ml" / "models" / "best_model.joblib")
        self.workspace_root = workspace_root or (get_project_root() / ".manet-workspace")
        self.config: dict[str, Any] = {}
        self.run_tag: str = ""
        self.scenario_name: str = "custom"
        self.seed: int = 42
        self.mode: str = "custom"
        self.validation_errors: list[str] = []

    def compose(self) -> ComposeResult:
        """Compose Step 3 pre-flight review layout."""
        yield Static(
            "[bold $primary]Step 3: Pre-Flight Review & Confirmation[/]\n"
            "[dim]Inspect verified parameters, champion model status, and target workspace path before allocation.[/]",
            id="review-header",
        )

        with Container(id="review-summary-card"):
            yield Static("Configuration Parameters Summary", classes="review-section-title")
            yield Static("", id="review-params-content")

        with Container(id="review-model-status-box", classes="model-ok"):
            yield Static("Champion Model Status", classes="review-section-title")
            yield Static("", id="review-model-content")

        with Container(id="review-workspace-box"):
            yield Static("Target Workspace Destination", classes="review-section-title")
            yield Static("", id="review-workspace-content")

        yield Static("", id="review-errors-display")

        with Container(id="review-actions"):
            yield Button("Back to Edit", id="btn-review-back")
            yield Button("Confirm & Allocate Run", variant="success", id="btn-review-launch")

    def update_review(
        self,
        config: dict[str, Any],
        run_tag: str,
        scenario_name: str,
        mode: str,
        model_path: Path | None = None,
    ) -> None:
        """Update review screen with verified configuration parameters and check invariants."""
        if model_path is not None:
            self.model_path = model_path

        self.config = config
        self.run_tag = run_tag
        self.scenario_name = scenario_name
        self.seed = int(config.get("seed", 42))
        self.mode = mode

        # Run Tier 2 validation
        self.validation_errors = validate_structural_invariants(config, model_path=self.model_path)

        # 1. Format configuration summary
        nodes = config.get("nodes", 30)
        duration = float(config.get("duration", 100.0))
        seed = int(config.get("seed", 42))
        attack_cfg = config.get("attack", {})
        attack_type = attack_cfg.get("type", "None") if isinstance(attack_cfg, dict) else "None"
        ids_cfg = config.get("ids", {})
        ids_enabled = bool(ids_cfg.get("enabled", False)) if isinstance(ids_cfg, dict) else False

        flows = config.get("flows", [])
        flow_count = len(flows) if isinstance(flows, list) else 1
        rate_pps = float(flows[0].get("rate_pps", 4.0)) if flows and isinstance(flows[0], dict) else 4.0
        estimated_packets = int(duration * rate_pps * max(flow_count, 1))

        radio_cfg = config.get("radio", {})
        radio_range = radio_cfg.get("range", 250.0) if isinstance(radio_cfg, dict) else 250.0
        loss_prob = radio_cfg.get("loss_probability", 0.0) if isinstance(radio_cfg, dict) else 0.0

        summary_text = (
            f"[bold]Scenario Name:[/] [bold $secondary]{escape(str(scenario_name))}[/]   "
            f"[bold]Mode:[/] {escape(str(mode)).upper()}\n"
            f"[bold]Nodes:[/] {nodes}   [bold]Duration:[/] {duration:.1f}s   "
            f"[bold]Explicit Seed:[/] {seed}   [bold]Attacker Strategy:[/] {escape(str(attack_type))}\n"
            f"[bold]Traffic Flows:[/] {flow_count} flow(s) @ {rate_pps:.1f} pps   "
            f"[bold]Estimated Packet Scale:[/] ~{estimated_packets:,} packets\n"
            f"[bold]Radio Range:[/] {radio_range}m   [bold]Channel Loss Probability:[/] {loss_prob}\n"
            f"[bold]IDS Mitigation:[/] {'[bold $success]ENABLED[/]' if ids_enabled else '[dim]DISABLED[/]'}"
        )
        self.query_one("#review-params-content", Static).update(summary_text)

        # 2. Check Champion Model Status
        model_box = self.query_one("#review-model-status-box")
        model_content = self.query_one("#review-model-content", Static)
        model_exists = False
        try:
            if self.model_path.is_file() and self.model_path.stat().st_size > 0:
                model_exists = True
        except Exception:
            model_exists = False

        if ids_enabled:
            if model_exists:
                model_box.remove_class("model-missing")
                model_box.add_class("model-ok")
                model_content.update(
                    f"[bold $success]CHAMPION MODEL PRESENT:[/] {escape(str(self.model_path))}\n"
                    f"[dim]Artifact verified on disk. OnlineIDS active isolation gate enabled.[/]"
                )
            else:
                model_box.remove_class("model-ok")
                model_box.add_class("model-missing")
                model_content.update(
                    "[bold $error]CHAMPION MODEL MISSING - IDS DISABLED[/]\n"
                    f"[dim]Model artifact {escape(str(self.model_path))} was not found on disk.[/]\n"
                    "[bold $warning]Remediation Command:[/] "
                    "[bold cyan]python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate[/]"
                )
        else:
            model_box.remove_class("model-missing")
            model_box.remove_class("model-ok")
            model_content.update("[dim]IDS mitigation is not active for this run.[/]")

        # 3. Workspace Path Preview (truthful pattern with configured workspace root)
        clean_scenario = re.sub(r'[\s\\/:*?"<>|]+', "_", str(scenario_name).strip()).strip("._") or "scenario"
        clean_tag = sanitize_run_tag(run_tag)
        preview_id = f"exp_<TIMESTAMP>_{clean_scenario}_{seed}"
        if clean_tag:
            preview_id = f"{preview_id}_{clean_tag}"
        preview_path = f"{self.workspace_root.as_posix().rstrip('/')}/{preview_id}/"

        workspace_content = self.query_one("#review-workspace-content", Static)
        workspace_content.update(
            f"[bold]Target Directory Pattern:[/] [bold $secondary]{escape(preview_path)}[/]\n"
            f"[dim]Allocated under {escape(str(self.workspace_root))}; exact timestamp and collision suffix are finalized at confirmation.[/]"
        )

        # 4. Check validation errors and set launch button disabled state
        btn_launch = self.query_one("#btn-review-launch", Button)
        errors_display = self.query_one("#review-errors-display", Static)

        if self.validation_errors:
            errors_display.update(
                "[bold $error]Launch Blocked by Invariant Errors:[/]\n"
                + "\n".join(f"• {escape(err)}" for err in self.validation_errors)
            )
            btn_launch.disabled = True
        else:
            errors_display.update("")
            btn_launch.disabled = False

    def show_error(self, message: str) -> None:
        """Display an actionable allocation or runtime error on the review screen."""
        errors_display = self.query_one("#review-errors-display", Static)
        errors_display.update(f"[bold $error]Launch Error:[/] {escape(message)}")
        btn_launch = self.query_one("#btn-review-launch", Button)
        btn_launch.disabled = True

    def reset_review(self) -> None:
        """Reset confirmation state and disable launch button."""
        try:
            btn_launch = self.query_one("#btn-review-launch", Button)
            btn_launch.disabled = True
            errors_display = self.query_one("#review-errors-display", Static)
            errors_display.update("")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Back to Edit and Confirm & Allocate Run buttons."""
        if event.button.id == "btn-review-back":
            self.post_message(self.ReviewBack())
        elif event.button.id == "btn-review-launch":
            self.action_confirm_launch()

    def action_confirm_launch(self) -> None:
        """Trigger launch confirmation if no validation errors exist."""
        btn_launch = self.query_one("#btn-review-launch", Button)
        if btn_launch.disabled:
            return
        self.post_message(
            self.ReviewConfirmed(
                config=self.config,
                run_tag=self.run_tag,
                scenario_name=self.scenario_name,
                seed=self.seed,
                mode=self.mode,
            )
        )


__all__ = ["StepReviewWidget"]
