"""AST architectural boundary tests enforcing presentation and command package isolation.

Verifies:
- manet/ modules never import business logic packages (simulator, attacks, feature_extraction, ml)
  per D-12 and TUI-02 (pure presentation layer, one-way contract).
- manet/commands/ modules never import OS process execution primitives (subprocess, shutil, os)
  per D-10, Pitfall 5, and T-7-01 (strict application-commands-only execution boundary).
"""

from __future__ import annotations

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


def test_manet_never_imports_business_packages():
    """Verify manet/ modules never import simulator, attacks, feature_extraction, or ml (D-12, TUI-02)."""
    repo_root = Path(__file__).resolve().parent.parent
    manet_dir = repo_root / "manet"
    assert manet_dir.exists(), f"manet directory does not exist at {manet_dir}"

    forbidden_roots = ("simulator", "attacks", "feature_extraction", "ml")
    py_files = sorted(manet_dir.rglob("*.py"))
    assert len(py_files) > 0, f"Expected python files in {manet_dir}"

    for py_file in py_files:
        imported = _get_imported_modules(py_file)
        violations = [
            imp
            for imp in imported
            if any(imp == root or imp.startswith(f"{root}.") for root in forbidden_roots)
        ]
        assert (
            len(violations) == 0
        ), f"Architectural violation (D-12/TUI-02): {py_file.relative_to(repo_root)} imports business packages: {violations}"

    # Specifically assert adapters, runtime, screens, and widgets subpackages exist and are covered
    for subpkg in ("adapters", "runtime", "screens", "widgets"):
        sub_dir = manet_dir / subpkg
        assert sub_dir.is_dir(), f"Expected subpackage directory {sub_dir} to exist"
        sub_py = list(sub_dir.glob("*.py"))
        assert len(sub_py) > 0, f"Expected python modules in {sub_dir}"


def test_business_packages_never_import_manet():
    """Verify simulator, attacks, feature_extraction, and ml never import manet (D-01)."""
    repo_root = Path(__file__).resolve().parent.parent
    business_pkgs = ("simulator", "attacks", "feature_extraction", "ml")

    for pkg in business_pkgs:
        pkg_dir = repo_root / pkg
        if not pkg_dir.exists():
            continue
        py_files = sorted(pkg_dir.rglob("*.py"))
        for py_file in py_files:
            imported = _get_imported_modules(py_file)
            violations = [
                imp
                for imp in imported
                if imp == "manet" or imp.startswith("manet.")
            ]
            assert (
                len(violations) == 0
            ), f"Bidirectional violation (D-01): {py_file.relative_to(repo_root)} imports manet: {violations}"

            # Verify get_project_root is never imported into simulator/
            if pkg == "simulator":
                assert (
                    "manet.runtime.paths" not in imported
                ), f"simulator module {py_file.relative_to(repo_root)} imports get_project_root"


def test_bootstrap_is_at_project_root():
    """Verify bootstrap.py exists strictly at the repository root and never inside manet/."""
    repo_root = Path(__file__).resolve().parent.parent
    bootstrap_root = repo_root / "bootstrap.py"
    bootstrap_inside_manet = repo_root / "manet" / "bootstrap.py"

    assert bootstrap_root.is_file(), f"Expected bootstrap.py at repo root {bootstrap_root}"
    assert not bootstrap_inside_manet.exists(), "bootstrap.py must not exist inside manet/ directory"


def test_command_package_never_uses_os_execution():
    """Verify manet/commands/ modules never import subprocess, shutil, or os (D-10, T-7-01, Pitfall 5)."""
    repo_root = Path(__file__).resolve().parent.parent
    commands_dir = repo_root / "manet" / "commands"
    assert commands_dir.exists(), f"commands directory does not exist at {commands_dir}"

    forbidden_roots = ("subprocess", "shutil", "os")
    py_files = sorted(commands_dir.rglob("*.py"))
    assert len(py_files) > 0, f"Expected python files in {commands_dir}"

    for py_file in py_files:
        imported = _get_imported_modules(py_file)
        violations = [
            imp
            for imp in imported
            if any(imp == root or imp.startswith(f"{root}.") for root in forbidden_roots)
        ]
        assert (
            len(violations) == 0
        ), (
            f"Security boundary violation (D-10/T-7-01/Pitfall 5): "
            f"{py_file.relative_to(repo_root)} imports OS execution primitives: {violations}. "
            f"The rule is never widened."
        )
