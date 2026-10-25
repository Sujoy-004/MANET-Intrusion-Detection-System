"""AST architectural boundary tests enforcing simulator never imports attacks."""

import ast
from pathlib import Path


def _get_imported_modules(file_path: Path) -> list[str]:
    """Extract all imported top-level module names from a Python source file using AST."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module)
    return imported


def test_core_simulator_never_imports_attacks():
    """Enforce AGENTS.md rule: simulator core modules must NEVER import from attacks."""
    repo_root = Path(__file__).resolve().parent.parent
    simulator_dir = repo_root / "simulator"

    core_modules = [
        "aodv.py",
        "mobility.py",
        "radio.py",
        "traffic.py",
        "metrics.py",
        "__init__.py",
    ]

    for mod_name in core_modules:
        mod_path = simulator_dir / mod_name
        assert mod_path.exists(), f"Expected module {mod_path} does not exist"
        imported = _get_imported_modules(mod_path)
        attack_imports = [imp for imp in imported if imp == "attacks" or imp.startswith("attacks.")]
        assert (
            len(attack_imports) == 0
        ), f"Architectural violation: {mod_name} imports attacks directly: {attack_imports}"


def test_only_run_scenario_acts_as_composition_root():
    """Verify run_scenario.py is the only simulator module permitted to import attacks."""
    repo_root = Path(__file__).resolve().parent.parent
    simulator_dir = repo_root / "simulator"

    for py_file in simulator_dir.glob("*.py"):
        imported = _get_imported_modules(py_file)
        attack_imports = [imp for imp in imported if imp == "attacks" or imp.startswith("attacks.")]
        if py_file.name == "run_scenario.py":
            # Allowed to import from attacks
            continue
        else:
            assert (
                len(attack_imports) == 0
            ), f"Module {py_file.name} violates boundary by importing {attack_imports}"


def test_attacks_package_never_imports_simulator():
    """Enforce architectural boundary: attacks package must not import simulator."""
    repo_root = Path(__file__).resolve().parent.parent
    attacks_dir = repo_root / "attacks"

    assert attacks_dir.exists(), "attacks directory does not exist"
    for py_file in attacks_dir.glob("*.py"):
        imported = _get_imported_modules(py_file)
        sim_imports = [imp for imp in imported if imp == "simulator" or imp.startswith("simulator.")]
        assert (
            len(sim_imports) == 0
        ), f"Architectural violation: attacks/{py_file.name} imports simulator: {sim_imports}"
