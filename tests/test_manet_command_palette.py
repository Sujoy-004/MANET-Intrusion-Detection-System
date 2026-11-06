"""Tests for the MANET IDS command palette provider and UI lifecycle.

Verifies:
- Registration of ManetCommands provider on ManetApp.COMMANDS
- Provider discover() yields all registry commands in deterministic insertion order
- Provider search("") yields the same result set as discover()
- Provider search() fuzzy-scores relevant commands and filters zero-score misses
- Registry-fidelity invariant (T-7-03): hit set matches registry commands exactly
- Hit callback execution routes truthfully through app action methods
- Keyboard lifecycle: ctrl+p opens CommandPalette, escape cleanly dismisses it
"""

from __future__ import annotations

import pytest
from textual.command import CommandPalette, DiscoveryHit, Hit

from manet.app import ManetApp
from manet.commands.palette_provider import ManetCommands
from manet.commands.registry import iter_known


def test_commands_registered_on_manet_app():
    """Verify ManetCommands provider is registered in ManetApp.COMMANDS."""
    assert ManetCommands in ManetApp.COMMANDS, (
        "ManetCommands provider not found in ManetApp.COMMANDS set"
    )


@pytest.mark.asyncio
async def test_discover_yields_all_registry_commands_in_order():
    """Verify discover() yields one DiscoveryHit per registry command in insertion order."""
    app = ManetApp()
    async with app.run_test():
        provider = ManetCommands(app.screen)
        hits = [hit async for hit in provider.discover()]
        expected_commands = iter_known()

        assert len(hits) == len(expected_commands), (
            f"Discovery hit count {len(hits)} does not match registry count {len(expected_commands)}"
        )

        for hit, expected in zip(hits, expected_commands):
            assert isinstance(hit, DiscoveryHit), f"Expected DiscoveryHit, got {type(hit)}"
            assert hit.display == expected.display, (
                f"Hit display '{hit.display}' does not match expected '{expected.display}'"
            )
            assert hit.help == expected.help, (
                f"Hit help '{hit.help}' does not match expected '{expected.help}'"
            )
            assert callable(hit.command), f"Hit callback for {expected.name} must be callable"


@pytest.mark.asyncio
async def test_empty_search_matches_discover():
    """Verify search('') yields identical hits to discover()."""
    app = ManetApp()
    async with app.run_test():
        provider = ManetCommands(app.screen)
        discover_hits = [hit async for hit in provider.discover()]
        empty_search_hits = [hit async for hit in provider.search("")]

        assert len(empty_search_hits) == len(discover_hits), (
            "Empty query search hit count does not match discover hit count"
        )
        assert [h.display for h in empty_search_hits] == [h.display for h in discover_hits], (
            "Empty query search display items do not match discover displays"
        )


@pytest.mark.asyncio
async def test_search_fuzzy_scoring_and_filtering():
    """Verify search() scores matching commands > 0 and filters out non-matching queries."""
    app = ManetApp()
    async with app.run_test():
        provider = ManetCommands(app.screen)

        # Matching query
        matching_hits = [hit async for hit in provider.search("work")]
        assert len(matching_hits) == 1, (
            f"Expected exactly 1 hit for 'work', got {len(matching_hits)}"
        )
        hit = matching_hits[0]
        assert isinstance(hit, Hit), f"Expected Hit instance, got {type(hit)}"
        assert hit.score > 0, f"Expected positive match score, got {hit.score}"
        assert str(hit.text) == "Go to workspace", (
            f"Unexpected matched hit text '{hit.text}'"
        )

        # Non-matching nonsense query
        miss_hits = [hit async for hit in provider.search("xyz999nonsense_unmatched")]
        assert len(miss_hits) == 0, (
            f"Expected 0 hits for nonsense query, got {len(miss_hits)}"
        )


@pytest.mark.asyncio
async def test_registry_fidelity_no_escape_or_phantom_hits():
    """Verify hit source displays match registry displays exactly with honest dispatch (T-7-03)."""
    app = ManetApp()
    async with app.run_test():
        provider = ManetCommands(app.screen)
        hits = [hit async for hit in provider.discover()]

        registry_commands = iter_known()
        registry_displays = {cmd.display for cmd in registry_commands}
        hit_displays = {hit.display for hit in hits}

        assert hit_displays == registry_displays, (
            f"Registry escape detected (T-7-03): provider hits {hit_displays} "
            f"differ from registry {registry_displays}"
        )

        # Introspect callback dispatch
        workspace_hit = next(h for h in hits if h.display == "Go to workspace")
        action_invoked = []
        app.action_show_workspace = lambda: action_invoked.append("invoked")

        workspace_hit.command()
        assert action_invoked == ["invoked"], (
            "Palette hit callback failed to dispatch to ManetApp.action_show_workspace"
        )


@pytest.mark.asyncio
async def test_command_palette_open_and_escape_cycle():
    """Verify ctrl+p opens CommandPalette and escape dismisses back to workspace."""
    app = ManetApp()
    async with app.run_test() as pilot:
        # Initial screen should be workspace
        assert not isinstance(app.screen, CommandPalette), (
            "CommandPalette must not be mounted initially"
        )

        # Open command palette with framework default ctrl+p
        await pilot.press("ctrl+p")
        await pilot.pause()
        assert isinstance(app.screen, CommandPalette), (
            f"Expected active screen to be CommandPalette, got {type(app.screen)}"
        )

        # Dismiss command palette with escape
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, CommandPalette), (
            "CommandPalette should be dismissed after escape key"
        )
        assert app.screen.__class__.__name__ == "MainWorkspace", (
            f"Expected active screen MainWorkspace after escape, got {type(app.screen)}"
        )
