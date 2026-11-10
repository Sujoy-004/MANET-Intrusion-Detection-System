"""Tests for safe workspace experiment pruning (TUI-21)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from manet.adapters.workspace import WorkspaceAdapter


def _make_exp(root: Path, name: str, files: dict[str, bytes]) -> Path:
    d = root / name
    d.mkdir(parents=True)
    for rel, data in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return d


def _try_symlink(target: Path, link: Path, *, target_is_directory: bool = False) -> bool:
    try:
        os.symlink(target, link, target_is_directory=target_is_directory)
        return True
    except (OSError, NotImplementedError):
        return False


def test_preview_deletion_recursive_enumeration(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(
        ws,
        "exp_a",
        {
            "manifest.json": b"{}",
            "trace.csv": b"a,b\n1,2\n",
            "sub/nested.txt": b"hi",
        },
    )
    adapter = WorkspaceAdapter(workspace_root=ws)
    preview = adapter.preview_experiment_deletion("exp_a")
    assert preview["experiment_id"] == "exp_a"
    assert preview["file_count"] == 3
    assert preview["total_bytes"] == sum(len(b) for b in [b"{}", b"a,b\n1,2\n", b"hi"])
    rels_norm = {f["relative_path"].replace("\\", "/") for f in preview["files"]}
    assert rels_norm == {"manifest.json", "trace.csv", "sub/nested.txt"}
    for f in preview["files"]:
        assert "content_sha256" in f and len(f["content_sha256"]) == 64
        assert "size_bytes" in f and "mtime_ns" in f
    assert "fingerprint" in preview and len(preview["fingerprint"]) == 64


def test_delete_experiment_run_safety(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    exp = _make_exp(ws, "exp_del", {"a.txt": b"hello"})
    adapter = WorkspaceAdapter(workspace_root=ws)
    preview = adapter.preview_experiment_deletion("exp_del")
    reclaimed = adapter.delete_experiment_run("exp_del", expected_preview=preview)
    assert reclaimed == len(b"hello")
    assert not exp.exists()


def test_stale_preview_rejection(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    exp = _make_exp(ws, "exp_stale", {"a.txt": b"hello"})
    adapter = WorkspaceAdapter(workspace_root=ws)
    preview = adapter.preview_experiment_deletion("exp_stale")
    (exp / "b.txt").write_bytes(b"new")
    with pytest.raises(RuntimeError, match="modified since deletion preview"):
        adapter.delete_experiment_run("exp_stale", expected_preview=preview)
    assert exp.exists()


def test_same_size_file_modification_detection(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    exp = _make_exp(ws, "exp_same", {"a.txt": b"abcde"})
    adapter = WorkspaceAdapter(workspace_root=ws)
    preview = adapter.preview_experiment_deletion("exp_same")
    (exp / "a.txt").write_bytes(b"fghij")  # same size, different content
    with pytest.raises(RuntimeError, match="modified since deletion preview"):
        adapter.delete_experiment_run("exp_stale2" if False else "exp_same", expected_preview=preview)
    assert exp.exists()


def test_symlinked_directory_rejection(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    real = ws / "real_exp"
    real.mkdir()
    (real / "a.txt").write_bytes(b"x")
    link = ws / "exp_link"
    if not _try_symlink(real, link, target_is_directory=True):
        pytest.skip("symlinks not supported")
    adapter = WorkspaceAdapter(workspace_root=ws)
    with pytest.raises(ValueError, match="Symlinked experiment directory is prohibited"):
        adapter.preview_experiment_deletion("exp_link")
    with pytest.raises(ValueError, match="Symlinked experiment directory is prohibited"):
        adapter.delete_experiment_run("exp_link")
    assert real.exists()


def test_internal_symlinked_directory_rejection(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    exp = _make_exp(ws, "exp_intdir", {"a.txt": b"x"})
    outside = tmp_path / "outside_dir"
    outside.mkdir()
    link = exp / "subdir"
    if not _try_symlink(outside, link, target_is_directory=True):
        pytest.skip("symlinks not supported")
    adapter = WorkspaceAdapter(workspace_root=ws)
    with pytest.raises(ValueError, match="Symlinked directory inside experiment directory is prohibited"):
        adapter.preview_experiment_deletion("exp_intdir")


def test_symlinked_file_rejection(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    exp = _make_exp(ws, "exp_intfile", {"a.txt": b"x"})
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"secret")
    link = exp / "linked.txt"
    if not _try_symlink(outside, link, target_is_directory=False):
        pytest.skip("symlinks not supported")
    adapter = WorkspaceAdapter(workspace_root=ws)
    with pytest.raises(ValueError, match="Symlinked file inside experiment directory is prohibited"):
        adapter.preview_experiment_deletion("exp_intfile")


def test_windows_file_lock_handling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_lock", {"a.txt": b"x"})
    adapter = WorkspaceAdapter(workspace_root=ws)
    preview = adapter.preview_experiment_deletion("exp_lock")

    import manet.adapters.workspace as workspace_mod

    def locked(*args: object, **kwargs: object) -> None:
        raise PermissionError("locked")

    monkeypatch.setattr(workspace_mod.shutil, "rmtree", locked)
    with pytest.raises(RuntimeError, match="files are locked by another Windows process"):
        adapter.delete_experiment_run("exp_lock", expected_preview=preview)


def test_delete_experiment_run_traversal_and_root(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_ok", {"a.txt": b"x"})
    adapter = WorkspaceAdapter(workspace_root=ws)
    # traversal-like name: resolved path check should catch attempts to escape
    with pytest.raises((ValueError, FileNotFoundError)):
        adapter.delete_experiment_run("../../scenarios")
    # cannot delete root - try via an id that resolves to root? Easier: use preview/delete on "."
    # The implementation should reject target == workspace root
    with pytest.raises((ValueError, FileNotFoundError, RuntimeError)):
        adapter.preview_experiment_deletion(".")

# ========================= Phase 11 Task 1: gitignore + modal tests =========================


def test_git_check_ignore_workspace(tmp_path: Path) -> None:
    """.gitignore isolates .manet-workspace/ via actual git check-ignore (TUI-21)."""
    repo_root = Path(__file__).resolve().parent.parent
    gitignore = repo_root / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert ".manet-workspace/" in content
    # preserve existing semantics
    assert "traces/" in content
    assert "data/" in content
    assert "results/*" in content
    result = subprocess.run(
        ["git", "check-ignore", ".manet-workspace/exp_1/trace.csv"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git check-ignore failed: {result.stdout} {result.stderr}"
    assert ".manet-workspace" in (result.stdout + result.stderr)


@pytest.mark.asyncio
async def test_prune_confirmation_modal_preview_composition() -> None:
    """PruneConfirmationModal renders preview and returns boolean confirmation."""
    from textual.app import App, ComposeResult
    from textual.widgets import Static

    from manet.screens.prune_modal import PruneConfirmationModal

    preview = {
        "experiment_id": "exp_test_42",
        "path": "/tmp/ws/exp_test_42",
        "files": [
            {"relative_path": "trace.csv", "size_bytes": 2048},
            {"relative_path": "manifest.json", "size_bytes": 512},
            {"relative_path": "isolation_log.csv", "size_bytes": 128},
        ],
        "total_bytes": 2688,
    }

    class ModalTestApp(App[bool | None]):
        def __init__(self) -> None:
            super().__init__()
            self.result: bool | None = None

        def on_mount(self) -> None:
            self.push_screen(PruneConfirmationModal(preview), self._capture)

        def _capture(self, value: bool | None) -> None:
            self.result = value
            self.exit(value)

    # Cancel via action
    app_cancel = ModalTestApp()
    async with app_cancel.run_test() as pilot:
        await pilot.pause(0.1)
        modal = app_cancel.screen
        assert isinstance(modal, PruneConfirmationModal)
        text = "\n".join(str(w.render()) for w in modal.query(Static))
        assert "exp_test_42" in text
        assert "trace.csv" in text
        assert "2.0 KB" in text or "2.00 KB" in text  # 2048 bytes
        assert "2688" in text or "2.6 KB" in text
        await pilot.press("escape")
        await pilot.pause(0.1)
    assert app_cancel.result is False

    # Confirm via Delete button
    app_confirm = ModalTestApp()
    async with app_confirm.run_test() as pilot:
        await pilot.pause(0.1)
        await pilot.click("#btn-delete")
        await pilot.pause(0.1)
    assert app_confirm.result is True

    # Confirm via immediate Enter key (verifying AUTO_FOCUS = "#btn-delete")
    app_enter = ModalTestApp()
    async with app_enter.run_test() as pilot:
        await pilot.pause(0.1)
        assert app_enter.screen.focused is not None
        assert app_enter.screen.focused.id == "btn-delete"
        await pilot.press("enter")
        await pilot.pause(0.1)
    assert app_enter.result is True

    # Cancel via Tab to Cancel button + Enter
    app_tab_cancel = ModalTestApp()
    async with app_tab_cancel.run_test() as pilot:
        await pilot.pause(0.1)
        await pilot.press("tab")
        await pilot.pause(0.1)
        assert app_tab_cancel.screen.focused is not None
        assert app_tab_cancel.screen.focused.id == "btn-cancel"
        await pilot.press("enter")
        await pilot.pause(0.1)
    assert app_tab_cancel.result is False


def test_delete_experiment_run_atomic_rollback_on_lock(tmp_path: Path) -> None:
    """Windows file-lock contention leaves experiment directory completely intact (G-11-2)."""
    ws = tmp_path / "ws"
    ws.mkdir()
    exp_dir = _make_exp(
        ws,
        "exp_atomic_lock",
        {
            "manifest.json": b'{"id": "exp_atomic_lock"}',
            "trace.csv": b"time,node_id,event\n0.1,1,send\n",
            "isolation_log.csv": b"time,node_id,reason\n",
        },
    )
    adapter = WorkspaceAdapter(workspace_root=ws)
    preview = adapter.preview_experiment_deletion("exp_atomic_lock")

    trace_file = exp_dir / "trace.csv"
    with open(trace_file, "r", encoding="utf-8") as _locked_handle:
        with pytest.raises(RuntimeError, match="files are locked by another Windows process"):
            adapter.delete_experiment_run("exp_atomic_lock", expected_preview=preview)

        # CRITICAL: Verify directory and ALL files are untouched and intact!
        assert exp_dir.exists(), "Target directory must not be deleted on locked failure"
        assert (exp_dir / "manifest.json").exists(), "manifest.json must remain intact"
        assert (exp_dir / "manifest.json").read_bytes() == b'{"id": "exp_atomic_lock"}'
        assert (exp_dir / "trace.csv").exists(), "trace.csv must remain intact"
        assert (exp_dir / "isolation_log.csv").exists(), "isolation_log.csv must remain intact"

    # Once handle is closed, deletion succeeds cleanly
    reclaimed = adapter.delete_experiment_run("exp_atomic_lock")
    assert not exp_dir.exists()
    assert reclaimed > 0

