"""Theme definitions for MANET IDS TUI.

Implements the D-06 cybersecurity/SOC semantic color contract:
- Cyan (#00b8d4): Navigation emphasis and active key shortcuts
- Blue (#3b82f6): Informational surfaces and status displays
- Green (#22c55e): Healthy system state and normal operations
- Amber (#f59e0b): Warnings, threshold alerts, and degraded operations
- Red (#ef4444): Critical alerts, attack detections, and intrusion errors

Semantic colors are defined both in standard framework slots and custom variables
to ensure TCSS references theme variables ($variable) rather than hardcoded hex values.
"""

from __future__ import annotations

from textual.theme import Theme

SOC = Theme(
    name="manet-soc",
    dark=True,
    background="#0a0f14",
    surface="#101820",
    panel="#152230",
    foreground="#dbe4ed",
    primary="#00b8d4",
    secondary="#3b82f6",
    accent="#22c55e",
    success="#22c55e",
    warning="#f59e0b",
    error="#ef4444",
    variables={
        "navigation-cyan": "#00b8d4",
        "info-blue": "#3b82f6",
        "healthy-green": "#22c55e",
        "warning-amber": "#f59e0b",
        "critical-red": "#ef4444",
        "footer-key-foreground": "#00b8d4",
    },
)

__all__ = ["SOC"]
