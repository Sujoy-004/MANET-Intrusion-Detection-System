"""Safe workspace pruning confirmation modal (TUI-21, D-04).

Presents an explicit, un-dismissible preview of files to be deleted and total
bytes to reclaim. Returns True (confirmed) or False (cancelled). This modal
NEVER performs disk deletion — HistoryScreen owns execution and error handling.
"""

from __future__ import annotations

from typing import Any

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class PruneConfirmationModal(ModalScreen[bool]):
    """Confirmation dialog for experiment record deletion.

    Returns True when the user explicitly confirms deletion, False when
    cancelled via [Esc] or the Cancel button. Does not execute deletion.
    """

    BINDINGS = [
        Binding("escape", "cancel_delete", "Cancel", show=True),
        Binding("enter", "confirm_delete", "Delete", show=True),
    ]

    DEFAULT_CSS = """
    PruneConfirmationModal {
        align: center middle;
    }

    #prune-dialog {
        width: 72;
        max-width: 90%;
        height: auto;
        max-height: 90%;
        border: thick #f85149;
        background: #161b22;
        padding: 1 2;
        color: #e6edf3;
    }

    #prune-title {
        text-style: bold;
        color: #f85149;
        margin-bottom: 1;
    }

    #prune-description {
        margin-bottom: 1;
    }

    #prune-file-list {
        margin-bottom: 1;
        padding: 0 1;
        color: #8b949e;
    }

    #prune-total {
        margin-bottom: 1;
    }

    #prune-buttons {
        layout: horizontal;
        align: right middle;
        height: 3;
        margin-top: 1;
    }

    #prune-buttons Button {
        margin-left: 1;
        min-width: 18;
    }
    """

    def __init__(self, preview: dict[str, Any], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.preview = preview or {}

    def compose(self) -> ComposeResult:
        preview = self.preview
        exp_id = escape(str(preview.get("experiment_id", "unknown")))
        dir_path = escape(str(preview.get("path", preview.get("directory_path", ""))))
        files = preview.get("files", []) or []
        total_bytes = int(preview.get("total_bytes", 0) or 0)
        total_kb = total_bytes / 1024.0

        file_lines = []
        for f in files:
            if not isinstance(f, dict):
                continue
            name = escape(str(f.get("relative_path") or f.get("name") or "file"))
            size_b = int(f.get("size_bytes", 0) or 0)
            size_kb = size_b / 1024.0
            file_lines.append(f"  • {name} ({size_kb:.1f} KB)")
        file_list_text = "\n".join(file_lines) if file_lines else "  • (no files)"

        with Vertical(id="prune-dialog"):
            yield Static("[bold #f85149]DELETE EXPERIMENT RECORD[/]", id="prune-title")
            yield Static(
                f"Experiment: [bold]{exp_id}[/]\nDirectory: {dir_path}\n\n"
                "[#d29922]This will permanently delete the following files:[/]",
                id="prune-description",
            )
            yield Static(file_list_text, id="prune-file-list")
            yield Static(
                f"Total space to reclaim: [bold green]{total_kb:.1f} KB[/] ({total_bytes} bytes)",
                id="prune-total",
            )
            with Horizontal(id="prune-buttons"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Delete Permanently", id="btn-delete", variant="error")

    def action_cancel_delete(self) -> None:
        """Dismiss without deletion."""
        self.dismiss(False)

    def action_confirm_delete(self) -> None:
        """Confirm deletion request (HistoryScreen performs actual deletion)."""
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.action_cancel_delete()
        elif event.button.id == "btn-delete":
            self.action_confirm_delete()


__all__ = ["PruneConfirmationModal"]
