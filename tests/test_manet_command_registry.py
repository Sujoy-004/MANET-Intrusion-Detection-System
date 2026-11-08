"""Tests for the MANET IDS application command registry.

Verifies:
- Command resolution for valid command names with exact parameter parsing
- Command resolution rejection for unknown command names
- Command resolution rejection for parameter-count mismatches
- Determinism and stability of iter_known() ordering across calls
- Anti-phantom-command honesty: every command action maps to an existing ManetApp method
- Action fields are string references only (never callables or executable objects)
"""

from __future__ import annotations

from manet.app import ManetApp
from manet.commands.registry import AppCommand, iter_known, resolve


def test_resolve_known_command():
    """Verify resolve succeeds for known command name with matching arguments."""
    res = resolve("workspace", [])
    assert res is not None, "Expected 'workspace' command to resolve successfully"
    cmd, params = res
    assert isinstance(cmd, AppCommand), f"Expected AppCommand instance, got {type(cmd)}"
    assert cmd.name == "workspace", f"Expected name 'workspace', got {cmd.name}"
    assert cmd.action == "action_show_workspace", (
        f"Expected action 'action_show_workspace', got {cmd.action}"
    )
    assert params == {}, f"Expected empty parameter dictionary, got {params}"


def test_resolve_unknown_command():
    """Verify resolve returns None for unknown command names."""
    res = resolve("no-such-command", [])
    assert res is None, f"Expected None for unknown command name, got {res}"


def test_resolve_argument_mismatch():
    """Verify resolve rejects calls with mismatched positional argument counts."""
    res = resolve("workspace", ["unexpected_arg"])
    assert res is None, (
        f"Expected None when passing extra arguments to parameterless command, got {res}"
    )


def test_iter_known_determinism():
    """Verify iter_known returns commands in deterministic insertion order across calls."""
    first_call = iter_known()
    second_call = iter_known()
    assert isinstance(first_call, tuple), f"Expected tuple, got {type(first_call)}"
    assert isinstance(second_call, tuple), f"Expected tuple, got {type(second_call)}"
    assert [cmd.name for cmd in first_call] == [cmd.name for cmd in second_call], (
        "Command sequence mismatch between consecutive iter_known() invocations"
    )
    assert first_call == second_call, "iter_known() tuples are not identical across calls"


def test_anti_phantom_command_honesty():
    """Verify every registered command action truthfully exists on ManetApp (T-7-02)."""
    commands = iter_known()
    assert len(commands) > 0, "Expected at least one command in registry"
    for cmd in commands:
        assert isinstance(cmd.action, str), f"Command {cmd.name} action must be str, got {type(cmd.action)}"
        assert not callable(cmd.action), f"Command {cmd.name} action must not be a callable object"
        assert not isinstance(cmd.action, (bytes, bytearray)), (
            f"Command {cmd.name} action must not be bytes"
        )
        assert hasattr(ManetApp, cmd.action), (
            f"Phantom command detected: ManetApp has no action method '{cmd.action}' "
            f"for command '{cmd.name}'"
        )


def test_resolve_parameterized_command_abstraction(monkeypatch):
    """Verify resolve() correctly handles parameterized commands and arity checks (IN-04)."""
    import manet.commands.registry as reg

    test_cmd = AppCommand(
        name="test:param",
        display="Test Parameterized Command",
        help="Command taking parameters",
        parameters=("param_a", "param_b"),
        action="action_test_param",
    )
    monkeypatch.setattr(reg, "_COMMANDS", (*reg._COMMANDS, test_cmd))

    # Exact argument count matches
    res = reg.resolve("test:param", ["foo", "bar"])
    assert res is not None
    cmd, params = res
    assert cmd == test_cmd
    assert params == {"param_a": "foo", "param_b": "bar"}

    # Under-arity: too few arguments
    assert reg.resolve("test:param", ["foo"]) is None

    # Over-arity: too many arguments
    assert reg.resolve("test:param", ["foo", "bar", "baz"]) is None
