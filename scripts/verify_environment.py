"""On-demand environment health verification for the MANET IDS project.

Validates the runtime environment a developer or CI runner needs before executing
the simulator, ML chain, or TUI. Checks performed:

1. Python runtime >= 3.11 (required).
2. The 10 pinned dependencies are importable AND installed at the exact version
   recorded in requirements.txt (required) - a version mismatch is a failure
   because the pins are the drift detector (T-12-03).
3. Project artifacts (scenarios/*.json, data/train.csv, data/test.csv,
   ml/models/best_model.joblib) reported [PRESENT]/[ABSENT] - informational
   only; a fresh checkout legitimately has no trained model yet.
4. CLI entrypoints smoke-checked via subprocess ``--help`` (required). The three
   argparse CLIs must exit 0. ``python -m manet --help`` launches the Textual
   application, which never exits when stdout/stderr are captured pipes (no
   interactive terminal), so the healthy signal there is "still running at the
   timeout"; a fast non-zero exit means the launcher failed to start.

Invariant: the exit code is 0 if and only if every required check (runtime,
dependency, entrypoint) succeeds. Artifact presence never affects the exit code.

Usage: python scripts/verify_environment.py
"""

from __future__ import annotations

import importlib
import importlib.metadata
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MIN_PYTHON = (3, 11)

# import name -> (PyPI distribution name, exact pinned version per requirements.txt)
PINNED_DEPENDENCIES: dict[str, tuple[str, str]] = {
    "simpy": ("simpy", "4.1.2"),
    "networkx": ("networkx", "3.6.1"),
    "sklearn": ("scikit-learn", "1.8.0"),
    "pandas": ("pandas", "3.0.2"),
    "numpy": ("numpy", "1.26.4"),
    "matplotlib": ("matplotlib", "3.10.8"),
    "seaborn": ("seaborn", "0.13.2"),
    "joblib": ("joblib", "1.5.3"),
    "textual": ("textual", "8.2.8"),
    "pytest": ("pytest", "9.0.2"),
}

# Informational artifact checks: (label, path relative to PROJECT_ROOT).
OPTIONAL_ARTIFACTS: list[tuple[str, str]] = [
    ("scenario configs (scenarios/*.json)", "scenarios"),
    ("training dataset (data/train.csv)", "data/train.csv"),
    ("test dataset (data/test.csv)", "data/test.csv"),
    ("champion model (ml/models/best_model.joblib)", "ml/models/best_model.joblib"),
]

# (display name, module path, timeout seconds, check mode)
# mode "exit_zero": argparse CLI, healthy iff the subprocess exits 0.
# mode "tui_alive": full-screen TUI launcher, healthy iff the process is still
# running at the timeout (a fast non-zero exit means it failed to launch).
ENTRYPOINTS: list[tuple[str, str, int, str]] = [
    ("simulator.run_scenario", "simulator.run_scenario", 60, "exit_zero"),
    ("ml.train", "ml.train", 60, "exit_zero"),
    ("ml.evaluate", "ml.evaluate", 60, "exit_zero"),
    ("manet (TUI launcher)", "manet", 30, "tui_alive"),
]


def check_python_version() -> bool:
    """Verify the running interpreter is Python 3.11+.

    Returns:
        True when the runtime satisfies the project floor, False otherwise.
    """
    print(f"[*] Python runtime: {sys.version.split()[0]} on {platform.platform()}")
    if sys.version_info < MIN_PYTHON:
        print(f"  [FAIL] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required.")
        return False
    print(f"  [OK] Python version is >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]}.")
    return True


def check_dependencies() -> bool:
    """Verify all 10 pinned dependencies import and match their exact pin.

    Importability is checked with importlib.import_module; the installed
    version is read from importlib.metadata (authoritative even when a module
    lacks a __version__ attribute) and compared with == against the pin.

    Returns:
        True when every dependency imports at the pinned version, False otherwise.
    """
    print("[*] Checking required dependencies (exact pin match)...")
    all_ok = True
    for module_name, (distribution, pinned_version) in PINNED_DEPENDENCIES.items():
        try:
            importlib.import_module(module_name)
        except ImportError as err:
            print(f"  [FAIL] {distribution} could not be imported: {err}")
            all_ok = False
            continue
        installed = importlib.metadata.version(distribution)
        if installed == pinned_version:
            print(f"  [OK] {distribution} == {installed}")
        else:
            print(
                f"  [FAIL] {distribution} version drift: installed {installed}, "
                f"pinned {pinned_version} (see requirements.txt)"
            )
            all_ok = False
    return all_ok


def report_artifacts() -> None:
    """Report operational artifact presence as [PRESENT]/[ABSENT] information only.

    Artifact absence is normal on a fresh checkout (datasets are generated and
    models trained on demand), so this never contributes to the exit code.
    """
    print("[*] Checking optional project artifacts (informational)...")
    for label, relative in OPTIONAL_ARTIFACTS:
        path = PROJECT_ROOT / relative
        if relative.endswith("scenarios"):
            present = path.is_dir() and any(path.glob("*.json"))
            detail = f"{len(list(path.glob('*.json')))} files" if present else "none"
        else:
            present = path.is_file()
            detail = ""
        state = "[PRESENT]" if present else "[ABSENT]"
        suffix = f" ({detail})" if detail else ""
        print(f"  {state} {label}{suffix}")
    print("  [INFO] Artifacts are optional; absence never fails this verification.")


def check_entrypoints() -> bool:
    """Smoke-check the four CLI entrypoints via subprocess ``--help``.

    Returns:
        True when every entrypoint shows healthy launch behavior, False otherwise.
    """
    print("[*] Checking CLI entrypoint help invocations...")
    all_ok = True
    for display, module_path, timeout_secs, mode in ENTRYPOINTS:
        cmd = [sys.executable, "-m", module_path, "--help"]
        name = f"python -m {module_path} --help"
        try:
            res = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=timeout_secs,
                check=False,
            )
        except subprocess.TimeoutExpired:
            # subprocess.run kills and reaps the child before re-raising.
            if mode == "tui_alive":
                # The Textual app launched and is awaiting an interactive
                # terminal; with captured pipes it never exits. This is the
                # healthy signal for the TUI launcher.
                print(f"  [OK] {display} (started; awaiting terminal - expected in non-tty)")
            else:
                print(f"  [FAIL] {name} timed out after {timeout_secs}s")
                all_ok = False
            continue
        except Exception as err:  # pragma: no cover - defensive
            print(f"  [FAIL] {name} could not be executed: {err}")
            all_ok = False
            continue
        if res.returncode == 0:
            print(f"  [OK] {name} (exit 0)")
        elif mode == "tui_alive":
            print(
                f"  [FAIL] {display} exited immediately with code {res.returncode}; "
                f"TUI launcher failed to start: {res.stderr.strip()[:200]}"
            )
            all_ok = False
        else:
            print(f"  [FAIL] {name} exited with code {res.returncode}")
            all_ok = False
    return all_ok


def main() -> int:
    """Run every check and return the process exit code.

    Returns:
        0 when all required checks (runtime, dependency, entrypoint) succeed,
        1 when any required check fails.
    """
    print("=" * 60)
    print("MANET IDS - Environment Verification")
    print("=" * 60)
    runtime_ok = check_python_version()
    dependencies_ok = check_dependencies()
    report_artifacts()
    entrypoints_ok = check_entrypoints()

    print("-" * 60)
    if runtime_ok and dependencies_ok and entrypoints_ok:
        print("[+] ENVIRONMENT VERIFICATION PASSED")
        return 0
    print("[-] ENVIRONMENT VERIFICATION FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
