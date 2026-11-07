"""Pilot and component tests for simulation workflow wizard steps and screen."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Collapsible, DataTable, Input, RadioButton, RadioSet, Select, Switch

from manet.adapters.scenario import ScenarioAdapter, ScenarioPreset
from manet.widgets.wizard_step_mode import StepModeSelectWidget
from manet.widgets.wizard_step_params import StepParamsWidget


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
