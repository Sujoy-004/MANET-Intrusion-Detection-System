"""Tests for safe workspace experiment pruning (TUI-21)."""

from __future__ import annotations

import json
import os
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
    rels = {f["relative_path"] for f in preview["files"]}
    assert rels == {"manifest.json", "trace.csv", os.path.join("sub", "nested.txt").replace("\\", "/") or "sub/nested.txt"}
    # normalize for windows
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
