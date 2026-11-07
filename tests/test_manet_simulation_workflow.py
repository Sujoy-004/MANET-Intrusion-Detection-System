"""Pilot and component tests for simulation workflow wizard steps and screen."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, Collapsible, DataTable, Input, RadioButton, RadioSet, Select, Static, Switch

from manet.adapters.scenario import ScenarioAdapter, ScenarioPreset
from manet.adapters.workspace import WorkspaceAdapter
from manet.app import ManetApp
from manet.screens.main_workspace import MainWorkspace
from manet.screens.simulation_workflow import SimulationWorkflowScreen
from manet.widgets.wizard_step_mode import StepModeSelectWidget
from manet.widgets.wizard_step_params import StepParamsWidget
from manet.widgets.wizard_step_review import StepReviewWidget


class DummyStep1App(App[None]):
    """Test harness app for Step 1 Mode Selection widget."""

    def __init__(self) -> None:
        super().__init__()
        self.mode_msgs: list[StepModeSelectWidget.ModeSelected] = []

    def compose(self) -> ComposeResult:
        yield StepModeSelectWidget(id="step-mode-select")

    def on_step_mode_select_widget_mode_selected(self, event: StepModeSelectWidget.ModeSelected) -> None:
        self.mode_msgs.append(event)


class DummyStep2App(App[None]):
    """Test harness app for Step 2 Parameter Configuration widget."""

    def __init__(self) -> None:
        super().__init__()
        self.submitted_msgs: list[StepParamsWidget.ParametersSubmitted] = []
        self.back_msgs: list[StepParamsWidget.ParametersBack] = []

    def compose(self) -> ComposeResult:
        yield StepParamsWidget(id="step-param-config")

    def on_step_params_widget_parameters_submitted(self, event: StepParamsWidget.ParametersSubmitted) -> None:
        self.submitted_msgs.append(event)

    def on_step_params_widget_parameters_back(self, event: StepParamsWidget.ParametersBack) -> None:
        self.back_msgs.append(event)


@pytest.mark.asyncio
async def test_wizard_steps_step1_mode_selection():
    """Verify Step 1 Mode Selection widget populates presets and emits ModeSelected."""
    app = DummyStep1App()

    async with app.run_test() as pilot:
        step1 = app.query_one("#step-mode-select", StepModeSelectWidget)
        table = step1.query_one("#table-presets", DataTable)

        # Ensure presets were loaded into table
        assert table.row_count > 0

        # Click Next button
        btn_next = step1.query_one("#btn-mode-next")
        btn_next.press()
        await pilot.pause()

        # Selected preset mode message received
        assert len(app.mode_msgs) == 1
        msg = app.mode_msgs[0]
        assert msg.mode == "preset"
        assert msg.preset is not None
        assert msg.preset.nodes >= 2

        # Switch to custom mode
        radio_custom = step1.query_one("#radio-custom", RadioButton)
        radio_custom.value = True
        await pilot.pause()

        assert step1.mode == "custom"
        assert step1.get_selected_preset() is None


@pytest.mark.asyncio
async def test_wizard_steps_step2_params_structure_and_blur_validation():
    """Verify Step 2 has 5 core dials, 1 Collapsible, validate_on=['blur'], and explicit seed."""
    app = DummyStep2App()

    async with app.run_test() as pilot:
        step2 = app.query_one("#step-param-config", StepParamsWidget)

        # 1. Check 5 core dials
        input_nodes = step2.query_one("#input-nodes", Input)
        input_duration = step2.query_one("#input-duration", Input)
        input_seed = step2.query_one("#input-seed", Input)
        select_attacker = step2.query_one("#select-attacker", Select)
        switch_ids = step2.query_one("#switch-ids", Switch)

        assert input_nodes.value == "30"
        assert input_duration.value == "100.0"
        assert input_seed.value == "42"  # Explicit seed default 42
        assert select_attacker.value == "None"
        assert switch_ids.value is False

        # 2. Check Collapsible advanced section
        collapsible = step2.query_one("#collapsible-advanced", Collapsible)
        assert collapsible.collapsed is True

        # Check advanced dials inside collapsible
        input_radio = step2.query_one("#input-radio-range", Input)
        input_loss = step2.query_one("#input-loss-prob", Input)
        input_min_speed = step2.query_one("#input-min-speed", Input)
        input_max_speed = step2.query_one("#input-max-speed", Input)
        input_pause = step2.query_one("#input-pause-time", Input)
        input_rate = step2.query_one("#input-rate-pps", Input)
        input_width = step2.query_one("#input-area-width", Input)
        input_height = step2.query_one("#input-area-height", Input)
        input_tag = step2.query_one("#input-run-tag", Input)

        # 3. Check validate_on=['blur'] on all validated inputs
        for inp in (
            input_nodes,
            input_duration,
            input_seed,
            input_radio,
            input_loss,
            input_min_speed,
            input_max_speed,
            input_pause,
            input_rate,
            input_width,
            input_height,
        ):
            assert inp.validate_on == {"blur"}, f"Input {inp.id} does not use validate_on=['blur']"

        # 4. Test loading preset updates values
        dummy_preset = ScenarioPreset(
            scenario_id="test_preset_50n",
            description="Test 50 nodes preset",
            nodes=50,
            duration=200.0,
            attack_type="Grayhole",
            flow_count=4,
            raw_config={
                "scenario_id": "test_preset_50n",
                "nodes": 50,
                "duration": 200.0,
                "seed": 999,
                "attack": {"enabled": True, "type": "Grayhole", "drop_prob": 0.6},
                "ids": {"enabled": True},
                "radio": {"range": 300.0, "loss_probability": 0.05},
                "mobility": {"speed_range": [2.0, 15.0], "pause_time": 5.0},
                "area": [1500, 1500],
                "flows": [{"flow_id": 0, "src": 0, "dst": 49, "rate_pps": 8.0}],
            },
        )
        step2.load_preset(dummy_preset)
        assert input_nodes.value == "50"
        assert input_duration.value == "200.0"
        assert input_seed.value == "999"
        assert select_attacker.value == "Grayhole"
        assert switch_ids.value is True
        assert input_radio.value == "300.0"
        assert input_rate.value == "8.0"


@pytest.mark.asyncio
async def test_wizard_steps_step2_submission_and_back():
    """Verify Step 2 submission emits ParametersSubmitted and Back emits ParametersBack."""
    app = DummyStep2App()

    async with app.run_test() as pilot:
        step2 = app.query_one("#step-param-config", StepParamsWidget)

        # Test submit
        btn_next = step2.query_one("#btn-params-next")
        btn_next.press()
        await pilot.pause()

        assert len(app.submitted_msgs) == 1
        msg = app.submitted_msgs[0]
        assert msg.config["nodes"] == 30
        assert msg.config["seed"] == 42
        assert msg.mode == "custom"

        # Test back
        btn_back = step2.query_one("#btn-params-back")
        btn_back.press()
        await pilot.pause()

        assert len(app.back_msgs) == 1


class DummyStep3App(App[None]):
    """Test harness app for Step 3 Pre-Flight Review widget."""

    def __init__(self, model_path: Path | None = None, workspace_root: Path | None = None) -> None:
        super().__init__()
        self.model_path = model_path
        self.workspace_root = workspace_root
        self.confirmed_msgs: list[StepReviewWidget.ReviewConfirmed] = []
        self.back_msgs: list[StepReviewWidget.ReviewBack] = []

    def compose(self) -> ComposeResult:
        yield StepReviewWidget(
            model_path=self.model_path,
            workspace_root=self.workspace_root,
            id="step-preflight-review",
        )

    def on_step_review_widget_review_confirmed(self, event: StepReviewWidget.ReviewConfirmed) -> None:
        self.confirmed_msgs.append(event)

    def on_step_review_widget_review_back(self, event: StepReviewWidget.ReviewBack) -> None:
        self.back_msgs.append(event)


class DummyWorkflowScreenApp(App[None]):
    """Test harness app for full SimulationWorkflowScreen."""

    def __init__(self, screen_instance: SimulationWorkflowScreen) -> None:
        super().__init__()
        self.screen_instance = screen_instance

    def compose(self) -> ComposeResult:
        yield self.screen_instance


@pytest.mark.asyncio
async def test_ids_gating(tmp_path: Path):
    """Verify IDS toggle is visually and operationally gated on champion model existence (TUI-12)."""
    missing_model = tmp_path / "missing_model.joblib"
    app = DummyStep3App(model_path=missing_model)

    async with app.run_test() as pilot:
        step3 = app.query_one("#step-preflight-review", StepReviewWidget)
        btn_launch = step3.query_one("#btn-review-launch", Button)

        # 1. Test when IDS is enabled and champion model is missing
        config_with_ids = {
            "scenario_id": "test_ids_sim",
            "nodes": 30,
            "duration": 100.0,
            "seed": 42,
            "flows": [{"src": 0, "dst": 29, "rate_pps": 4.0}],
            "ids": {"enabled": True},
        }
        step3.update_review(
            config=config_with_ids,
            run_tag="test_tag",
            scenario_name="test_ids_sim",
            mode="custom",
            model_path=missing_model,
        )
        await pilot.pause()

        # Launch button must be strictly disabled
        assert btn_launch.disabled is True
        model_content = step3.query_one("#review-model-content", Static)
        errors_display = step3.query_one("#review-errors-display", Static)
        assert "CHAMPION MODEL MISSING" in str(model_content.render())
        assert "python scripts/build_dataset.py" in str(model_content.render())
        assert "Launch Blocked" in str(errors_display.render())

        # 2. Test when champion model exists on disk
        present_model = tmp_path / "best_model.joblib"
        present_model.write_bytes(b"mock_joblib_model_content_12345")

        step3.update_review(
            config=config_with_ids,
            run_tag="test_tag",
            scenario_name="test_ids_sim",
            mode="custom",
            model_path=present_model,
        )
        await pilot.pause()

        # Launch button must now be enabled
        assert btn_launch.disabled is False
        assert "CHAMPION MODEL PRESENT" in str(model_content.render())
        assert str(errors_display.render()) == ""

        # 3. Test when IDS is disabled
        config_no_ids = dict(config_with_ids)
        config_no_ids["ids"] = {"enabled": False}
        step3.update_review(
            config=config_no_ids,
            run_tag="test_tag",
            scenario_name="test_no_ids_sim",
            mode="custom",
            model_path=missing_model,
        )
        await pilot.pause()

        # Launch button must be enabled even if model is missing when IDS is disabled
        assert btn_launch.disabled is False
        assert "not active" in str(model_content.render())


@pytest.mark.asyncio
async def test_review_confirmation(tmp_path: Path):
    """Verify pre-flight review confirmation allocates directory and writes manifest (TUI-13, TUI-14)."""
    ws_root = tmp_path / ".manet-workspace"
    ws_adapter = WorkspaceAdapter(workspace_root=ws_root)
    workflow_screen = SimulationWorkflowScreen(workspace_adapter=ws_adapter)
    app = DummyWorkflowScreenApp(workflow_screen)

    async with app.run_test() as pilot:
        # Step 1: Mode Select -> Click Next
        btn_mode_next = app.query_one("#btn-mode-next", Button)
        btn_mode_next.press()
        await pilot.pause()

        # Step 2: Params Config -> Set custom run tag and click Next
        input_tag = app.query_one("#input-run-tag", Input)
        input_tag.value = "pilot_run"
        btn_params_next = app.query_one("#btn-params-next", Button)
        btn_params_next.press()
        await pilot.pause()

        # Step 3: Review Screen -> Click Confirm & Allocate Run
        btn_launch = app.query_one("#btn-review-launch", Button)
        assert btn_launch.disabled is False
        btn_launch.press()
        await pilot.pause()

        # Verify launch request populated on screen
        assert workflow_screen.launch_request is not None
        req = workflow_screen.launch_request
        assert req.scenario_name != ""
        assert req.seed == 42
        assert "pilot_run" in req.experiment_id
        assert req.workspace_dir.is_dir()

        # Verify manifest.json written
        manifest_path = req.workspace_dir / "manifest.json"
        assert manifest_path.is_file()
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["experiment_id"] == req.experiment_id
        assert manifest["seed"] == 42
        assert manifest["status"] == "CONFIGURED"
        assert manifest["software_version"] == "2.0.0-dev"
        assert "configuration" in manifest


@pytest.mark.asyncio
async def test_step1_preset_selection_and_parameter_population():
    """Verify selecting e1_normal_30n in Step 1 populates Step 2 form parameters (TUI-09)."""
    workflow_screen = SimulationWorkflowScreen()
    app = DummyWorkflowScreenApp(workflow_screen)

    async with app.run_test() as pilot:
        step1 = app.query_one("#step-mode-select", StepModeSelectWidget)
        table = step1.query_one("#table-presets", DataTable)

        # Find row for e1_normal_30n
        preset = step1.scenario_adapter.get_preset("e1_normal_30n")
        assert preset is not None
        assert preset.nodes == 30
        assert preset.duration == 300.0

        step1._selected_preset_id = "e1_normal_30n"
        btn_next = step1.query_one("#btn-mode-next", Button)
        btn_next.press()
        await pilot.pause()

        # Step 2 form should now match e1_normal_30n
        step2 = app.query_one("#step-param-config", StepParamsWidget)
        assert step2.query_one("#input-nodes", Input).value == "30"
        assert step2.query_one("#input-duration", Input).value == "300.0"
        assert step2.query_one("#select-attacker", Select).value == "None"


@pytest.mark.asyncio
async def test_step2_blur_validation_and_seed_customization():
    """Verify typing does not flash premature errors, invalid blur prevents submit, and custom seed persists (TUI-10, TUI-11)."""
    workflow_screen = SimulationWorkflowScreen()
    app = DummyWorkflowScreenApp(workflow_screen)

    async with app.run_test() as pilot:
        # Advance from Step 1 to Step 2
        app.query_one("#btn-mode-next", Button).press()
        await pilot.pause()

        step2 = app.query_one("#step-param-config", StepParamsWidget)
        input_nodes = step2.query_one("#input-nodes", Input)
        input_seed = step2.query_one("#input-seed", Input)
        error_display = step2.query_one("#params-error-display", Static)

        # 1. Typing an invalid value does NOT flash error prematurely while typing
        input_nodes.value = "1"
        assert str(error_display.render()) == ""

        # Blur the input
        input_seed.focus()
        await pilot.pause()
        # Even after blur, error display remains clean until submission
        assert str(error_display.render()) == ""

        # 2. Attempting to advance with invalid input blocks and updates error display
        btn_next = step2.query_one("#btn-params-next", Button)
        btn_next.press()
        await pilot.pause()

        assert "Validation Error" in str(error_display.render())
        # Current screen must remain step-param-config
        switcher = app.query_one("#wizard-switcher")
        assert switcher.current == "step-param-config"

        # 3. Correct node count and customize explicit seed
        input_nodes.value = "45"
        input_seed.value = "777888"
        btn_next.press()
        await pilot.pause()

        # Successfully advanced to step-preflight-review
        assert switcher.current == "step-preflight-review"

        # 4. Step back via Escape and verify custom seed and nodes are retained
        await pilot.press("escape")
        await pilot.pause()

        assert switcher.current == "step-param-config"
        assert input_nodes.value == "45"
        assert input_seed.value == "777888"


@pytest.mark.asyncio
async def test_wizard_escape_navigation_cycle():
    """Verify pressing Escape steps back across all wizard steps and returns to workspace (D-01)."""
    app = ManetApp()

    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)

        # Press 's' to open SimulationWorkflowScreen
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SimulationWorkflowScreen)

        workflow_screen = app.screen
        switcher = workflow_screen.query_one("#wizard-switcher")
        assert switcher.current == "step-mode-select"

        # Advance Step 1 -> Step 2
        await pilot.press("enter")
        await pilot.pause()
        assert switcher.current == "step-param-config"

        # Advance Step 2 -> Step 3
        await pilot.press("enter")
        await pilot.pause()
        assert switcher.current == "step-preflight-review"

        # Press Escape -> Step 3 to Step 2
        await pilot.press("escape")
        await pilot.pause()
        assert switcher.current == "step-param-config"

        # Press Escape -> Step 2 to Step 1
        await pilot.press("escape")
        await pilot.pause()
        assert switcher.current == "step-mode-select"

        # Press Escape -> Step 1 dismisses to MainWorkspace
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)


@pytest.mark.asyncio
async def test_collapsible_advanced_toggle():
    """Verify collapsible advanced parameters container expands and collapses cleanly (D-03)."""
    step2 = StepParamsWidget()
    app = DummyStep2App()

    async with app.run_test() as pilot:
        collapsible = app.query_one("#collapsible-advanced", Collapsible)
        assert collapsible.collapsed is True

        # Expand collapsible
        collapsible.collapsed = False
        await pilot.pause()
        assert collapsible.collapsed is False

        # Collapse again
        collapsible.collapsed = True
        await pilot.pause()
        assert collapsible.collapsed is True


