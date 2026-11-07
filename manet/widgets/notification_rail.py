"""Persistent notification rail widget fulfilling D-05 mounting contract."""

from __future__ import annotations

from textual.widgets import Static

from manet.adapters.notifications import NotificationAdapter


class NotificationRail(Static):
    """Notification rail displaying dismissible alert notices from NotificationAdapter."""

    def __init__(
        self,
        *args,
        adapter: NotificationAdapter | None = None,
        id: str | None = "notification-rail",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        self.adapter = adapter or NotificationAdapter()
        super().__init__("", *args, id=id, classes=classes, **kwargs)
        self._render_notice()

    def notify_user(self, text: str, level: str = "info") -> None:
        """Enqueue and display a notification message."""
        self.adapter.add_notice(text, level=level)
        self._render_notice()

    def dismiss(self) -> None:
        """Dismiss active notice."""
        self.adapter.clear()
        self._render_notice()

    def get_active_notice(self) -> str | None:
        """Return the current active notice text."""
        return self.adapter.get_active_notice()

    def _render_notice(self) -> None:
        """Update display based on active notice queue."""
        active = self.adapter.get_active_notice()
        if active:
            content = f" [bold $warning]⚠ NOTICE:[/] {active}  [dim](Press Esc to dismiss)[/]"
            self.update(content)
            self.display = True
        else:
            self.update("")
            self.display = False


__all__ = ["NotificationRail"]
