"""Tests for MANET IDS TUI theme switching, SOC contrast palettes, and session settings.

Verifies:
- Both standard 'manet-soc' and high-contrast 'manet-soc-high-contrast' themes are registered.
- Dynamic theme switching via action_toggle_high_contrast() toggles app.theme and session settings.
- action_toggle_reduced_motion() toggles session settings motion flag.
- Both themes provide identical semantic color variable keys ($navigation-cyan, $info-blue, etc.).
- AST analysis enforces D-09 constraint: manet/runtime/settings.py performs zero disk I/O,
  imports no serialization or file modules, and contains no persistence primitives.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from manet.app import ManetApp
from manet.runtime.settings import SessionSettings
from manet.runtime.theme import AI_STUDIO_WARM, SOC, SOC_HIGH_CONTRAST


REQUIRED_SEMANTIC_KEYS = (
    "navigation-cyan",
    "info-blue",
    "healthy-green",
    "warning-amber",
    "critical-red",
    "footer-key-foreground",
)


@pytest.mark.asyncio
async def test_theme_toggle_action_and_settings():
    """Verify action_toggle_high_contrast dynamically swaps themes and updates SessionSettings."""
    app = ManetApp()
    async with app.run_test() as pilot:
        # Initial mounted theme must be default SOC
        assert app.theme == "manet-soc"
        assert isinstance(app.settings, SessionSettings)
        assert app.settings.high_contrast is False

        # Toggle to high contrast
        app.action_toggle_high_contrast()
        await pilot.pause()

        assert app.settings.high_contrast is True
        assert app.theme == "manet-soc-high-contrast"

        # Toggle back to standard SOC
        app.action_toggle_high_contrast()
        await pilot.pause()

        assert app.settings.high_contrast is False
        assert app.theme == "manet-soc"


@pytest.mark.asyncio
async def test_reduced_motion_toggle_action():
    """Verify action_toggle_reduced_motion toggles the in-memory reduced_motion setting."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert app.settings.reduced_motion is False

        app.action_toggle_reduced_motion()
        await pilot.pause()
        assert app.settings.reduced_motion is True

        app.action_toggle_reduced_motion()
        await pilot.pause()
        assert app.settings.reduced_motion is False


@pytest.mark.asyncio
async def test_warm_theme_toggle_action():
    """Verify action_toggle_warm_theme toggles between SOC and Google AI Studio warm-white theme."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert app.theme == "manet-soc"

        app.action_toggle_warm_theme()
        await pilot.pause()
        assert app.theme == "manet-ai-studio-warm"

        app.action_toggle_warm_theme()
        await pilot.pause()
        assert app.theme == "manet-soc"


def test_theme_semantic_variables():
    """Verify all mandatory semantic color variables exist across themes (D-06, D-08)."""
    assert SOC.name == "manet-soc"
    assert SOC.dark is True
    assert SOC_HIGH_CONTRAST.name == "manet-soc-high-contrast"
    assert SOC_HIGH_CONTRAST.dark is True
    assert SOC_HIGH_CONTRAST.background == "#000000"
    assert AI_STUDIO_WARM.name == "manet-ai-studio-warm"
    assert AI_STUDIO_WARM.dark is False
    assert AI_STUDIO_WARM.background == "#f9f9f6"
    assert AI_STUDIO_WARM.surface == "#ffffff"

    for key in REQUIRED_SEMANTIC_KEYS:
        assert key in SOC.variables, f"Missing semantic variable '{key}' in SOC theme"
        assert key in SOC_HIGH_CONTRAST.variables, (
            f"Missing semantic variable '{key}' in SOC_HIGH_CONTRAST theme"
        )
        assert key in AI_STUDIO_WARM.variables, (
            f"Missing semantic variable '{key}' in AI_STUDIO_WARM theme"
        )


def test_session_settings_ast_zero_disk_io():
    """Verify manet/runtime/settings.py contains zero disk I/O or persistence imports (D-09)."""
    settings_path = (
        Path(__file__).resolve().parent.parent / "manet" / "runtime" / "settings.py"
    )
    assert settings_path.exists(), f"Settings file not found: {settings_path}"

    with open(settings_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=str(settings_path))

    forbidden_modules = {
        "os",
        "shutil",
        "pickle",
        "json",
        "sqlite3",
        "pathlib",
        "shelve",
        "dbm",
        "csv",
    }
    forbidden_calls = {"open", "write_text", "write_bytes", "dump", "dumps"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                assert mod not in forbidden_modules, (
                    f"D-09 violation: settings.py imports forbidden persistence module '{alias.name}'"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split(".")[0]
                assert mod not in forbidden_modules, (
                    f"D-09 violation: settings.py imports from forbidden module '{node.module}'"
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls, (
                    f"D-09 violation: settings.py calls forbidden file operation '{node.func.id}()'"
                )
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls, (
                    f"D-09 violation: settings.py calls forbidden method '.{node.func.attr}()'"
                )
