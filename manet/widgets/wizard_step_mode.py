"""Step 1: Scenario and mode selection widget for the simulation workflow wizard."""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.message import Message
from textual.widgets import (
    Button,
    DataTable,
    RadioButton,
    RadioSet,
    Static,
)

from manet.adapters.scenario import ScenarioAdapter, ScenarioPreset


class StepModeSelectWidget(VerticalScroll):
    """Step 1: Scenario & Mode Selection.

    Allows switching between authentic presets discovered from scenarios/*.json
    and custom simulation configuration.
    """

    class ModeSelected(Message):
        """Message emitted when user completes Step 1 and requests advancing to Step 2."""

        def __init__(self, mode: str, preset: ScenarioPreset | None = None) -> None:
            super().__init__()
            self.mode = mode  # "preset" or "custom"
            self.preset = preset

    DEFAULT_CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    StepModeSelectWidget {
        height: 1fr;
        padding: 1 2;
        background: $surface;
    }

    #step1-header {
        margin-bottom: 1;
    }

    #mode-radios {
        margin-bottom: 1;
        background: $panel;
        padding: 0 1;
        border: solid $info-blue;
    }

    #presets-container {
        height: auto;
        min-height: 8;
        max-height: 12;
        margin-bottom: 1;
        border: solid $info-blue;
        background: $panel;
    }

    #table-presets {
        height: 1fr;
    }

    #custom-info-container {
        display: none;
        padding: 1;
        margin-bottom: 1;
        border: solid $info-blue;
        background: $panel;
    }

    #mode-actions {
        layout: horizontal;
        height: auto;
        align: right middle;
        margin-top: 1;
    }

    #btn-mode-next {
        min-width: 28;
    }
    """

    COLUMNS = ("Scenario ID", "Nodes", "Duration (s)", "Attack", "Flows", "Description")

    def __init__(
        self,
        *args,
        scenario_adapter: ScenarioAdapter | None = None,
        id: str | None = "step-mode-select",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, id=id, classes=classes, **kwargs)
        self.scenario_adapter = scenario_adapter or ScenarioAdapter()
        self.mode: str = "preset"
        self._presets: list[ScenarioPreset] = []
        self._selected_preset_id: str | None = None
        self._columns_initialized: bool = False

    def compose(self) -> ComposeResult:
        """Compose Step 1 UI hierarchy."""
        yield Static(
            "[bold $primary]Step 1: Scenario & Mode Selection[/]\n"
            "[dim]Choose an authentic preset scenario from disk or configure a custom simulation.[/]",
            id="step1-header",
        )

        with RadioSet(id="mode-radios"):
            yield RadioButton("Preset Scenario (authentic scenarios/*.json)", value=True, id="radio-preset")
            yield RadioButton("Custom Simulation (manual configuration)", value=False, id="radio-custom")

        with Container(id="presets-container"):
            yield DataTable(id="table-presets", cursor_type="row", zebra_stripes=True)
            yield Static("", id="presets-diagnostic-notice")

        with Container(id="custom-info-container"):
            yield Static(
                "[bold $secondary]Custom Simulation Mode[/]\n"
                "[dim]You will configure node count, duration, explicit random seed, attack strategy,\n"
                "and optional advanced network dials in Step 2.[/]",
                id="custom-info-text",
            )

        with Container(id="mode-actions"):
            yield Button("Next: Configure Parameters", variant="primary", id="btn-mode-next")

    def on_mount(self) -> None:
        """Populate preset scenarios into DataTable."""
        self._ensure_columns()
        self.refresh_presets()

    def _ensure_columns(self) -> None:
        """Initialize columns in DataTable if not already added."""
        if not self._columns_initialized:
            table = self.query_one("#table-presets", DataTable)
            for col in self.COLUMNS:
                table.add_column(col, key=col.lower().replace(" ", "_").replace("(", "").replace(")", ""))
            self._columns_initialized = True

    def refresh_presets(self) -> None:
        """Discover presets via ScenarioAdapter and fill DataTable."""
        self._ensure_columns()
        table = self.query_one("#table-presets", DataTable)
        table.clear()
        self._presets = self.scenario_adapter.list_presets()

        seen_keys: set[str] = set()
        for preset in self._presets:
            if preset.scenario_id in seen_keys:
                continue
            table.add_row(
                escape(preset.scenario_id),
                str(preset.nodes),
                f"{preset.duration:.1f}",
                escape(preset.attack_type),
                str(preset.flow_count),
                escape(preset.description),
                key=preset.scenario_id,
            )
            seen_keys.add(preset.scenario_id)

        try:
            diag_widget = self.query_one("#presets-diagnostic-notice", Static)
            if self.scenario_adapter.diagnostics:
                diag_widget.update(
                    "[dim $warning]Notice: " + escape(" | ".join(self.scenario_adapter.diagnostics)) + "[/]"
                )
            else:
                diag_widget.update("")
        except Exception:
            pass

        if self._presets and self._selected_preset_id is None:
            self._selected_preset_id = self._presets[0].scenario_id

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Toggle display between preset table and custom description."""
        presets_box = self.query_one("#presets-container")
        custom_box = self.query_one("#custom-info-container")

        if event.pressed.id == "radio-preset":
            self.mode = "preset"
            presets_box.styles.display = "block"
            custom_box.styles.display = "none"
        else:
            self.mode = "custom"
            presets_box.styles.display = "none"
            custom_box.styles.display = "block"

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Capture user row selection in preset table."""
        if event.row_key and event.row_key.value:
            self._selected_preset_id = str(event.row_key.value)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Track highlighted row key as current candidate."""
        if event.row_key and event.row_key.value:
            self._selected_preset_id = str(event.row_key.value)

    @property
    def selected_preset(self) -> ScenarioPreset | None:
        """Property alias for get_selected_preset()."""
        return self.get_selected_preset()

    def get_selected_preset(self) -> ScenarioPreset | None:
        """Retrieve the currently selected ScenarioPreset record."""
        if self.mode != "preset":
            return None
        if self._selected_preset_id:
            for p in self._presets:
                if p.scenario_id == self._selected_preset_id:
                    return p
        return self._presets[0] if self._presets else None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Next button press."""
        if event.button.id == "btn-mode-next":
            self.action_submit_mode()

    def action_submit_mode(self) -> None:
        """Submit mode selection and post ModeSelected message."""
        preset = self.get_selected_preset() if self.mode == "preset" else None
        self.post_message(self.ModeSelected(mode=self.mode, preset=preset))


__all__ = ["StepModeSelectWidget"]
