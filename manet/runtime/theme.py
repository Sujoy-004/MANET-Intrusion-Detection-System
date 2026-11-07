"""Theme definitions for MANET IDS TUI.

Implements sky-blue dark minimalist design complying with D-06 semantic color contract:
- Sky-Blue / Cyan (#38bdf8): Navigation emphasis, focus indicators, and active key shortcuts
- Sky / Light Blue (#7dd3fc): Informational surfaces, borders, and status displays
- Emerald / Green (#34d399): Healthy system state and normal operations
- Amber (#fbbf24): Warnings, threshold alerts, and degraded operations
- Coral / Red (#f87171): Critical alerts, attack detections, and intrusion errors

Also provides SOC_HIGH_CONTRAST for enhanced visual contrast and accessibility (D-08, TUI-05),
featuring pitch-black background, ultra-high-contrast panels, and high-visibility sky-blue indicators.

Semantic colors are defined both in standard framework slots and custom variables
to ensure TCSS references theme variables ($variable) rather than hardcoded hex values.
"""

from __future__ import annotations

from textual.theme import Theme

SOC = Theme(
    name="manet-soc",
    dark=True,
    background="#0a0f18",
    surface="#101726",
    panel="#182338",
    foreground="#f0f6fc",
    primary="#38bdf8",
    secondary="#7dd3fc",
    accent="#38bdf8",
    success="#34d399",
    warning="#fbbf24",
    error="#f87171",
    variables={
        "navigation-cyan": "#38bdf8",
        "info-blue": "#7dd3fc",
        "healthy-green": "#34d399",
        "warning-amber": "#fbbf24",
        "critical-red": "#f87171",
        "footer-key-foreground": "#38bdf8",
    },
)

SOC_HIGH_CONTRAST = Theme(
    name="manet-soc-high-contrast",
    dark=True,
    background="#000000",
    surface="#070c14",
    panel="#0f1d33",
    foreground="#ffffff",
    primary="#7dd3fc",
    secondary="#38bdf8",
    accent="#4ade80",
    success="#4ade80",
    warning="#fde047",
    error="#fca5a5",
    variables={
        "navigation-cyan": "#7dd3fc",
        "info-blue": "#bae6fd",
        "healthy-green": "#4ade80",
        "warning-amber": "#fde047",
        "critical-red": "#fca5a5",
        "footer-key-foreground": "#7dd3fc",
    },
)

AI_STUDIO_WARM = Theme(
    name="manet-ai-studio-warm",
    dark=False,
    background="#f9f9f6",
    surface="#ffffff",
    panel="#f1f0ea",
    foreground="#1f1f1f",
    primary="#1a73e8",
    secondary="#0b57d0",
    accent="#7c3aed",
    success="#137333",
    warning="#b06000",
    error="#c5221f",
    variables={
        "navigation-cyan": "#1a73e8",
        "info-blue": "#0b57d0",
        "healthy-green": "#137333",
        "warning-amber": "#b06000",
        "critical-red": "#c5221f",
        "footer-key-foreground": "#1a73e8",
    },
)

__all__ = ["SOC", "SOC_HIGH_CONTRAST", "AI_STUDIO_WARM"]
