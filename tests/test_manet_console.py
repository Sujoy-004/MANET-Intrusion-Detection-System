"""Unit tests for ConsoleDriver execution, parameter validation, and in-memory history.

Verifies:
- Execution of registered application commands (e.g. 'workspace').
- Rejection of OS shell commands (ls, dir, rm, cat) and unknown commands.
- Parameter mismatch detection and usage formatting.
- In-memory bounded history navigation (prev / next).
- Absence of disk persistence and OS execution imports.
"""

from __future__ import annotations

import inspect
from manet.commands.console_driver import ConsoleDriver, ConsoleResult
import manet.commands.console_driver as console_driver_mod


class DummyApp:
    """Mock application frame for testing ConsoleDriver actions."""

    def __init__(self) -> None:
        self.workspace_invoked = False

    def action_show_workspace(self) -> None:
        self.workspace_invoked = True


def test_console_executes_workspace_command():
    """Verify executing known 'workspace' command triggers app action and returns success."""
    app = DummyApp()
    driver = ConsoleDriver(app=app)

    res = driver.execute("workspace")
    assert isinstance(res, ConsoleResult)
    assert res.success is True
    assert "Executed: Go to workspace" in res.output
    assert res.command is not None
    assert res.command.name == "workspace"
    assert app.workspace_invoked is True
    assert len(driver.history) == 1
    assert driver.history[0] == "workspace"


def test_console_rejects_unknown_and_os_commands():
    """Verify console rejects OS shell commands and unknown inputs without executing them."""
    app = DummyApp()
    driver = ConsoleDriver(app=app)

    for shell_cmd in ["ls", "dir", "rm -rf /", "cat /etc/passwd"]:
        res = driver.execute(shell_cmd)
        assert res.success is False
        assert f"Unknown command '{shell_cmd.split()[0]}'" in res.output
        assert "Type 'help' or check command palette." in res.output
        assert res.command is None

    # History only records executed commands, so failed commands were not added
    assert len(driver.history) == 0


def test_console_parameter_mismatch_validation():
    """Verify console returns parameter usage when argument arity does not match command."""
    app = DummyApp()
    driver = ConsoleDriver(app=app)

    # 'workspace' takes 0 arguments; passing extra arguments should fail
    res = driver.execute("workspace extra_arg")
    assert res.success is False
    assert "Parameter mismatch for 'workspace'" in res.output
    assert "no arguments" in res.output


def test_console_empty_input():
    """Verify empty or whitespace-only input returns neutral result without modifying history."""
    app = DummyApp()
    driver = ConsoleDriver(app=app)

    res = driver.execute("   ")
    assert res.success is True
    assert res.output == ""
    assert len(driver.history) == 0


def test_console_in_memory_history_navigation():
    """Verify in-memory history navigation works with prev/next and bounded deque."""
    app = DummyApp()
    driver = ConsoleDriver(app=app, max_history=3)

    # History initially empty
    assert driver.history_prev() is None
    assert driver.history_next() is None

    # Execute commands (for testing history navigation, append directly or execute valid)
    driver.execute("workspace")
    assert len(driver.history) == 1

    # Simulate additional history entries
    driver.history.append("cmd1")
    driver.history.append("cmd2")
    driver._history_index = len(driver.history)

    # Navigating back
    assert driver.history_prev() == "cmd2"
    assert driver.history_prev() == "cmd1"
    assert driver.history_prev() == "workspace"
    # Clamping at earliest
    assert driver.history_prev() == "workspace"

    # Navigating forward
    assert driver.history_next() == "cmd1"
    assert driver.history_next() == "cmd2"
    # At end of history, returns empty string for current uncommitted line
    assert driver.history_next() == ""
    assert driver.history_next() is None


def test_console_driver_zero_disk_persistence():
    """Verify ConsoleDriver maintains no file paths, file handles, or disk persistence."""
    app = DummyApp()
    driver = ConsoleDriver(app=app)

    # Check instance attributes
    attrs = vars(driver)
    for name, val in attrs.items():
        assert "path" not in name.lower()
        assert "file" not in name.lower()
        assert not hasattr(val, "write")


def test_console_driver_has_no_os_execution_imports():
    """Verify console_driver source code never imports subprocess, os, or shutil."""
    source = inspect.getsource(console_driver_mod)
    assert "subprocess" not in source
    assert "shutil" not in source
    assert "os." not in source
    assert "import os" not in source
