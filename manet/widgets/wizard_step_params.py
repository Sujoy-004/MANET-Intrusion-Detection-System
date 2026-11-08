"""Step 2: Simulation parameter configuration widget with progressive disclosure."""

from __future__ import annotations

import copy
from typing import Any

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.message import Message
from textual.validation import Integer, Number
from textual.widgets import (
    Button,
    Collapsible,
    Input,
    Label,
    Select,
    Static,
    Switch,
)

from manet.adapters.scenario import ScenarioPreset
from manet.adapters.simulation_config import (
    DEFAULT_AREA,
    DEFAULT_CUSTOM_DURATION,
    DEFAULT_LOSS_PROBABILITY,
    DEFAULT_PAUSE_TIME,
    DEFAULT_RADIO_RANGE,
    DEFAULT_RATE_PPS,
    DEFAULT_SEED,
    DEFAULT_SPEED_RANGE,
    MAX_DURATION,
    MAX_NODES,
    MIN_DURATION,
    MIN_NODES,
    build_custom_configuration,
)


class StepParamsWidget(VerticalScroll):
    """Step 2: Parameter Configuration.

    Displays 5 core macro dials and a Collapsible container for advanced network knobs.
    All validated inputs use validate_on=['blur'] to prevent premature error flashes.
    """

    class ParametersSubmitted(Message):
        """Emitted when parameters are valid and user requests advancing to review."""

        def __init__(
            self,
            config: dict[str, Any],
            run_tag: str,
            scenario_name: str,
            mode: str,
        ) -> None:
            super().__init__()
            self.config = config
            self.run_tag = run_tag
            self.scenario_name = scenario_name
            self.mode = mode

    class ParametersBack(Message):
        """Emitted when user requests returning to Step 1."""

        pass

    DEFAULT_CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    StepParamsWidget {
        height: 1fr;
        padding: 1 2;
        background: $surface;
    }

    #params-header {
        margin-bottom: 1;
    }

    #params-mode-indicator {
        margin-bottom: 1;
        padding: 0 1;
        background: $panel;
        color: $info-blue;
    }

    .form-row {
        height: auto;
        margin-bottom: 1;
    }

    .field-label {
        width: 28;
        color: $foreground;
        text-style: bold;
    }

    .field-input {
        width: 1fr;
    }

    #collapsible-advanced {
        margin-top: 1;
        margin-bottom: 1;
        border: solid $info-blue;
        background: $panel;
    }

    #params-error-display {
        height: auto;
        color: $error;
        margin-top: 1;
        margin-bottom: 1;
    }

    #params-actions {
        layout: horizontal;
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    #btn-params-back {
        margin-right: 2;
        min-width: 14;
    }

    #btn-params-next {
        min-width: 28;
    }
    """

    def __init__(
        self,
        *args,
        id: str | None = "step-param-config",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, id=id, classes=classes, **kwargs)
        self.mode: str = "custom"
        self.preset: ScenarioPreset | None = None

    def compose(self) -> ComposeResult:
        """Compose Step 2 form hierarchy."""
        yield Static(
            "[bold $primary]Step 2: Parameter Configuration[/]\n"
            "[dim]Configure core simulation dials and optional advanced network parameters.\n"
            "Form inputs validate on blur without flashing premature errors.[/]",
            id="params-header",
        )

        yield Static("[dim]Mode: Custom Simulation[/]", id="params-mode-indicator")

        # Core Form (5 dials)
        with Container(id="core-params-box"):
            # 1. Node Count
            with Horizontal(classes="form-row"):
                yield Label("Node Count (2-100):", classes="field-label")
                yield Input(
                    value=str(30),
                    validators=[Integer(minimum=MIN_NODES, maximum=MAX_NODES)],
                    validate_on=["blur"],
                    id="input-nodes",
                    classes="field-input",
                )

            # 2. Duration
            with Horizontal(classes="form-row"):
                yield Label("Duration in sec (10-3600):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_CUSTOM_DURATION),
                    validators=[Number(minimum=MIN_DURATION, maximum=MAX_DURATION)],
                    validate_on=["blur"],
                    id="input-duration",
                    classes="field-input",
                )

            # 3. Random Seed
            with Horizontal(classes="form-row"):
                yield Label("Random Seed (deterministic):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_SEED),
                    validators=[Integer(minimum=0, maximum=2147483647)],
                    validate_on=["blur"],
                    id="input-seed",
                    classes="field-input",
                )

            # 4. Attacker Strategy
            with Horizontal(classes="form-row"):
                yield Label("Attacker Strategy:", classes="field-label")
                yield Select.from_values(
                    ["None", "Blackhole", "Grayhole"],
                    value="None",
                    id="select-attacker",
                    classes="field-input",
                )

            # 5. IDS Mitigation
            with Horizontal(classes="form-row"):
                yield Label("IDS Mitigation Toggle:", classes="field-label")
                yield Switch(value=False, id="switch-ids")

        # Collapsible Advanced Section
        with Collapsible(title="Advanced Network Parameters", collapsed=True, id="collapsible-advanced"):
            with Horizontal(classes="form-row"):
                yield Label("Radio Range (10-2000m):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_RADIO_RANGE),
                    validators=[Number(minimum=10.0, maximum=2000.0)],
                    validate_on=["blur"],
                    id="input-radio-range",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("Loss Probability (0.0-1.0):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_LOSS_PROBABILITY),
                    validators=[Number(minimum=0.0, maximum=1.0)],
                    validate_on=["blur"],
                    id="input-loss-prob",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("Min Speed (m/s):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_SPEED_RANGE[0]),
                    validators=[Number(minimum=0.0, maximum=100.0)],
                    validate_on=["blur"],
                    id="input-min-speed",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("Max Speed (m/s):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_SPEED_RANGE[1]),
                    validators=[Number(minimum=0.1, maximum=100.0)],
                    validate_on=["blur"],
                    id="input-max-speed",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("Pause Time (0-3600s):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_PAUSE_TIME),
                    validators=[Number(minimum=0.0, maximum=3600.0)],
                    validate_on=["blur"],
                    id="input-pause-time",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("CBR Packet Rate (pps) [Override]:", classes="field-label")
                yield Input(
                    value=str(DEFAULT_RATE_PPS),
                    validators=[Number(minimum=0.1, maximum=1000.0)],
                    validate_on=["blur"],
                    id="input-rate-pps",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("Area Width (m):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_AREA[0]),
                    validators=[Integer(minimum=100, maximum=10000)],
                    validate_on=["blur"],
                    id="input-area-width",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("Area Height (m):", classes="field-label")
                yield Input(
                    value=str(DEFAULT_AREA[1]),
                    validators=[Integer(minimum=100, maximum=10000)],
                    validate_on=["blur"],
                    id="input-area-height",
                    classes="field-input",
                )

            with Horizontal(classes="form-row"):
                yield Label("Optional Run Tag:", classes="field-label")
                yield Input(
                    value="",
                    placeholder="e.g. baseline_test",
                    id="input-run-tag",
                    classes="field-input",
                )

        yield Static("", id="params-error-display")

        with Container(id="params-actions"):
            yield Button("Back", id="btn-params-back")
            yield Button("Next: Pre-Flight Review", variant="primary", id="btn-params-next")

    def load_preset(self, preset: ScenarioPreset) -> None:
        """Populate form inputs using an authentic ScenarioPreset."""
        self.mode = "preset"
        self.preset = preset

        indicator = self.query_one("#params-mode-indicator", Static)
        indicator.update(f"[bold $secondary]Loaded Preset:[/] {escape(preset.scenario_id)} - {escape(preset.description)}")

        self.query_one("#input-nodes", Input).value = str(preset.nodes)
        self.query_one("#input-duration", Input).value = str(preset.duration)

        raw_cfg = preset.raw_config
        self.query_one("#input-seed", Input).value = str(raw_cfg.get("seed", DEFAULT_SEED))

        attack_type = preset.attack_type.capitalize()
        if attack_type not in ("Blackhole", "Grayhole"):
            attack_type = "None"
        self.query_one("#select-attacker", Select).value = attack_type

        ids_cfg = raw_cfg.get("ids", {})
        ids_enabled = ids_cfg.get("enabled", False) if isinstance(ids_cfg, dict) else False
        self.query_one("#switch-ids", Switch).value = bool(ids_enabled)

        # Advanced network knobs
        radio_cfg = raw_cfg.get("radio", {})
        if isinstance(radio_cfg, dict):
            self.query_one("#input-radio-range", Input).value = str(radio_cfg.get("range", DEFAULT_RADIO_RANGE))
            self.query_one("#input-loss-prob", Input).value = str(radio_cfg.get("loss_probability", DEFAULT_LOSS_PROBABILITY))

        mobility_cfg = raw_cfg.get("mobility", {})
        if isinstance(mobility_cfg, dict):
            speed_range = mobility_cfg.get("speed_range", DEFAULT_SPEED_RANGE)
            if isinstance(speed_range, (list, tuple)) and len(speed_range) >= 2:
                self.query_one("#input-min-speed", Input).value = str(speed_range[0])
                self.query_one("#input-max-speed", Input).value = str(speed_range[1])
            self.query_one("#input-pause-time", Input).value = str(mobility_cfg.get("pause_time", DEFAULT_PAUSE_TIME))

        area = raw_cfg.get("area", DEFAULT_AREA)
        if isinstance(area, (list, tuple)) and len(area) >= 2:
            self.query_one("#input-area-width", Input).value = str(area[0])
            self.query_one("#input-area-height", Input).value = str(area[1])

        flows = raw_cfg.get("flows", [])
        if flows and isinstance(flows, list) and isinstance(flows[0], dict):
            init_rate = float(flows[0].get("rate_pps", DEFAULT_RATE_PPS))
        else:
            init_rate = float(DEFAULT_RATE_PPS)
        self._preset_initial_rate = init_rate
        self._rate_manually_edited = False
        self.query_one("#input-rate-pps", Input).value = str(init_rate)

        self.query_one("#input-run-tag", Input).value = ""
        self.query_one("#params-error-display", Static).update("")

    def set_custom_defaults(self) -> None:
        """Reset form inputs to standard benchmark defaults."""
        self.mode = "custom"
        self.preset = None
        self._rate_manually_edited = True

        indicator = self.query_one("#params-mode-indicator", Static)
        indicator.update("[dim]Mode: Custom Simulation (Manual Configuration)[/]")

        self.query_one("#input-nodes", Input).value = str(30)
        self.query_one("#input-duration", Input).value = str(DEFAULT_CUSTOM_DURATION)
        self.query_one("#input-seed", Input).value = str(DEFAULT_SEED)
        self.query_one("#select-attacker", Select).value = "None"
        self.query_one("#switch-ids", Switch).value = False

        self.query_one("#input-radio-range", Input).value = str(DEFAULT_RADIO_RANGE)
        self.query_one("#input-loss-prob", Input).value = str(DEFAULT_LOSS_PROBABILITY)
        self.query_one("#input-min-speed", Input).value = str(DEFAULT_SPEED_RANGE[0])
        self.query_one("#input-max-speed", Input).value = str(DEFAULT_SPEED_RANGE[1])
        self.query_one("#input-pause-time", Input).value = str(DEFAULT_PAUSE_TIME)
        self.query_one("#input-rate-pps", Input).value = str(DEFAULT_RATE_PPS)
        self.query_one("#input-area-width", Input).value = str(DEFAULT_AREA[0])
        self.query_one("#input-area-height", Input).value = str(DEFAULT_AREA[1])
        self.query_one("#input-run-tag", Input).value = ""
        self.query_one("#params-error-display", Static).update("")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Track manual changes to fields like CBR packet rate override."""
        if event.input.id == "input-rate-pps" and self.mode == "preset":
            try:
                val = float(event.value)
                init_val = getattr(self, "_preset_initial_rate", None)
                if init_val is not None and abs(val - init_val) > 1e-6:
                    self._rate_manually_edited = True
            except (ValueError, TypeError):
                self._rate_manually_edited = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Back and Next button actions."""
        if event.button.id == "btn-params-back":
            self.post_message(self.ParametersBack())
        elif event.button.id == "btn-params-next":
            self.action_submit_parameters()

    def action_submit_parameters(self) -> None:
        """Validate all form fields and post ParametersSubmitted if valid."""
        error_display = self.query_one("#params-error-display", Static)
        validated_inputs = self.query(Input)
        invalid_fields = []
        for inp in validated_inputs:
            if inp.validators:
                for v in inp.validators:
                    res = v.validate(inp.value)
                    if not res.is_valid:
                        invalid_fields.append(inp.id or "unknown")
                        break

        if invalid_fields:
            error_display.update(
                f"[bold $error]Validation Error:[/] Please correct invalid fields before proceeding: "
                f"{', '.join(invalid_fields)}"
            )
            return

        try:
            nodes = int(self.query_one("#input-nodes", Input).value)
            duration = float(self.query_one("#input-duration", Input).value)
            seed = int(self.query_one("#input-seed", Input).value)
            attacker_val = self.query_one("#select-attacker", Select).value
            attacker = str(attacker_val) if attacker_val != Select.NULL else "None"
            ids_enabled = bool(self.query_one("#switch-ids", Switch).value)

            radio_range = float(self.query_one("#input-radio-range", Input).value)
            loss_prob = float(self.query_one("#input-loss-prob", Input).value)
            min_speed = float(self.query_one("#input-min-speed", Input).value)
            max_speed = float(self.query_one("#input-max-speed", Input).value)
            pause_time = float(self.query_one("#input-pause-time", Input).value)
            rate_pps = float(self.query_one("#input-rate-pps", Input).value)
            area_w = int(self.query_one("#input-area-width", Input).value)
            area_h = int(self.query_one("#input-area-height", Input).value)
            run_tag = self.query_one("#input-run-tag", Input).value.strip()
        except (ValueError, TypeError) as exc:
            error_display.update(f"[bold $error]Input Error:[/] {escape(str(exc))}")
            return

        if min_speed >= max_speed:
            error_display.update(
                f"[bold $error]Validation Error:[/] Mobility minimum speed ({min_speed}) must be strictly less than maximum speed ({max_speed})."
            )
            return

        error_display.update("")

        if self.mode == "preset" and self.preset is not None:
            config = copy.deepcopy(self.preset.raw_config)
            config["nodes"] = nodes
            config["duration"] = duration
            config["seed"] = seed
            if "radio" not in config or not isinstance(config["radio"], dict):
                config["radio"] = {}
            config["radio"]["range"] = radio_range
            config["radio"]["loss_probability"] = loss_prob

            if "mobility" not in config or not isinstance(config["mobility"], dict):
                config["mobility"] = {}
            config["mobility"]["speed_range"] = [min_speed, max_speed]
            config["mobility"]["pause_time"] = pause_time

            config["area"] = [area_w, area_h]

            is_rate_overridden = getattr(self, "_rate_manually_edited", False)
            if hasattr(self, "_preset_initial_rate") and abs(rate_pps - self._preset_initial_rate) > 1e-6:
                is_rate_overridden = True

            bad_flows = []
            if "flows" in config and isinstance(config["flows"], list):
                for idx, flow in enumerate(config["flows"]):
                    if isinstance(flow, dict):
                        src = flow.get("src", 0)
                        dst = flow.get("dst", 0)
                        if src < 0 or src >= nodes or dst < 0 or dst >= nodes or src == dst:
                            bad_flows.append((idx, src, dst))
                        elif is_rate_overridden:
                            flow["rate_pps"] = rate_pps

            if bad_flows:
                bad_descs = [f"Flow #{i} ({s}->{d})" for i, s, d in bad_flows]
                error_display.update(
                    f"[bold $error]Flow Endpoints Error:[/] Preset flows use endpoints outside valid range [0, {nodes - 1}]: "
                    f"{', '.join(bad_descs)}. Increase node count to at least match preset endpoints or select custom mode."
                )
                return

            is_attack = attacker.lower() not in ("none", "")
            if "attack" not in config or not isinstance(config["attack"], dict):
                config["attack"] = {}
            config["attack"]["enabled"] = is_attack
            config["attack"]["type"] = attacker if is_attack else "None"

            if "ids" not in config or not isinstance(config["ids"], dict):
                config["ids"] = {}
            config["ids"]["enabled"] = ids_enabled

            scenario_name = self.preset.scenario_id
        else:
            advanced_params = {
                "radio_range": radio_range,
                "loss_probability": loss_prob,
                "speed_range": [min_speed, max_speed],
                "pause_time": pause_time,
                "rate_pps": rate_pps,
                "area": [area_w, area_h],
            }
            config = build_custom_configuration(
                nodes=nodes,
                duration=duration,
                seed=seed,
                attack_type=attacker,
                ids_enabled=ids_enabled,
                advanced_params=advanced_params,
            )
            scenario_name = config.get("scenario_id", f"custom_{nodes}n")

        self.post_message(
            self.ParametersSubmitted(
                config=config,
                run_tag=run_tag,
                scenario_name=scenario_name,
                mode=self.mode,
            )
        )


__all__ = ["StepParamsWidget"]
