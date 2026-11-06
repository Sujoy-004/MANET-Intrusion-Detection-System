"""Application command package for MANET IDS TUI.

This package exposes application commands only. No module in this package may
import subprocess, shutil, or os, and no command may construct a process.
"""

from __future__ import annotations

from manet.commands.console_driver import ConsoleDriver, ConsoleResult
from manet.commands.palette_provider import ManetCommands
from manet.commands.registry import AppCommand, iter_known, resolve

__all__ = [
    "AppCommand",
    "ConsoleDriver",
    "ConsoleResult",
    "ManetCommands",
    "iter_known",
    "resolve",
]
