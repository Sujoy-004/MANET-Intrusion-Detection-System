"""Tests for experiment manifest artifact hashing, integrity verification, and metadata (TUI-20)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from manet.adapters.workspace import (
    ExperimentSummary,
    WorkspaceAdapter,
    compute_experiment_artifacts,
    get_experiment_manifest,
    record_launch_manifest,
    update_manifest_status,
    verify_artifact_checksums,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_tracer_manifest_hash_and_verify(tmp_path: Path) -> None:
    """Tracer: finalization records chunked SHA-256 artifacts and verify returns VERIFIED."""
    exp_dir = tmp_path / "exp_20240101_120000_test_scenario_42_exp-test"
    exp_dir.mkdir(parents=True)
    trace_content = b"time,src,dst,pkt_id,type\n1.0,0,1,1,DATA\n2.0,1,0,2,ACK\n"
    (exp_dir / "trace.csv").write_bytes(trace_content)
    (exp_dir / "manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": exp_dir.name,
                "scenario_name": "test_scenario",
                "seed": 42,
                "tag": "exp-test",
                "status": "RUNNING",
                "created_at": "2024-01-01T12:00:00+00:00",
                "configuration": {"tag": "exp-test"},
            }
        ),
        encoding="utf-8",
    )

    update_manifest_status(exp_dir, "COMPLETED", metrics={"pdr": 0.95})

    manifest = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
    assert "artifacts" in manifest
    art = manifest["artifacts"]["trace.csv"]
    assert len(art["sha256"]) == 64
    assert art["sha256"] == _sha256_bytes(trace_content)
    assert art["relative_path"] == "trace.csv"
    assert art["size_bytes"] == len(trace_content)
    assert manifest.get("tag") == "exp-test"
    assert art["row_count"] == 2  # 3 lines total minus header

    result = WorkspaceAdapter().verify_artifact_checksums(exp_dir)
    assert result["trace.csv"]["status"] == "VERIFIED"
    assert result["trace.csv"]["expected_sha256"] == art["sha256"]
    assert result["trace.csv"]["current_sha256"] == art["sha256"]


def test_artifact_tamper_detection(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp_tamper"
    exp_dir.mkdir()
    (exp_dir / "trace.csv").write_text("h1,h2\na,b\n", encoding="utf-8")
    (exp_dir / "manifest.json").write_text(
        json.dumps({"experiment_id": "exp_tamper", "status": "RUNNING"}), encoding="utf-8"
    )
    update_manifest_status(exp_dir, "COMPLETED")

    r1 = verify_artifact_checksums(exp_dir)
    assert r1["trace.csv"]["status"] == "VERIFIED"

    (exp_dir / "trace.csv").write_text("h1,h2\na,b\nc,d\n", encoding="utf-8")
    r2 = verify_artifact_checksums(exp_dir)
    assert r2["trace.csv"]["status"] == "CORRUPTED"
    assert r2["trace.csv"]["expected_sha256"] != r2["trace.csv"]["current_sha256"]

    (exp_dir / "trace.csv").unlink()
    r3 = verify_artifact_checksums(exp_dir)
    assert r3["trace.csv"]["status"] == "MISSING"


def test_legacy_manifest_recorded_state(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp_legacy"
    exp_dir.mkdir()
    content = b"time,val\n1,2\n"
    (exp_dir / "trace.csv").write_bytes(content)
    # Manifest without artifacts key
    (exp_dir / "manifest.json").write_text(
        json.dumps({"experiment_id": "exp_legacy", "status": "COMPLETED"}), encoding="utf-8"
    )
    r = verify_artifact_checksums(exp_dir)
    assert r["trace.csv"]["status"] == "RECORDED"
    assert r["trace.csv"]["expected_sha256"] is None
    assert r["trace.csv"]["current_sha256"] == _sha256_bytes(content)


def test_csv_and_json_row_count_semantics(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp_rows"
    exp_dir.mkdir()
    (exp_dir / "trace.csv").write_text("h1,h2\na,b\nc,d\n", encoding="utf-8")  # 3 lines -> 2 data rows
    (exp_dir / "isolation_log.csv").write_text("", encoding="utf-8")  # empty
    (exp_dir / "isolation_log.json").write_text('[{"a":1},{"a":2},{"a":3}]', encoding="utf-8")
    (exp_dir / "manifest.json").write_text(
        json.dumps({"experiment_id": "exp_rows", "status": "RUNNING"}), encoding="utf-8"
    )
    update_manifest_status(exp_dir, "COMPLETED")
    m = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
    assert m["artifacts"]["trace.csv"]["row_count"] == 2
    assert m["artifacts"]["isolation_log.csv"]["row_count"] == 0
    assert m["artifacts"]["isolation_log.json"]["row_count"] == 3

    # JSON dict should not use newline count
    exp_dir2 = tmp_path / "exp_jsondict"
    exp_dir2.mkdir()
    (exp_dir2 / "isolation_log.json").write_text('{"events": [1,2]}\n', encoding="utf-8")
    (exp_dir2 / "manifest.json").write_text(
        json.dumps({"experiment_id": "exp_jsondict", "status": "RUNNING"}), encoding="utf-8"
    )
    update_manifest_status(exp_dir2, "COMPLETED")
    m2 = json.loads((exp_dir2 / "manifest.json").read_text(encoding="utf-8"))
    assert m2["artifacts"]["isolation_log.json"]["row_count"] is None


def test_malformed_and_missing_manifests(tmp_path: Path) -> None:
    assert get_experiment_manifest(tmp_path / "nope") is None
    exp_dir = tmp_path / "exp_bad"
    exp_dir.mkdir()
    assert get_experiment_manifest(exp_dir) is None
    (exp_dir / "manifest.json").write_text("{not json", encoding="utf-8")
    assert get_experiment_manifest(exp_dir) is None
    (exp_dir / "manifest.json").write_text("[]", encoding="utf-8")
    assert get_experiment_manifest(exp_dir) is None


def test_unsafe_artifact_paths_boundary(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp_safe"
    exp_dir.mkdir()
    outside = tmp_path / "evil.txt"
    outside.write_text("secret", encoding="utf-8")
    (exp_dir / "manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": "exp_safe",
                "artifacts": {
                    "trace.csv": {
                        "filename": "trace.csv",
                        "relative_path": "../evil.txt",
                        "sha256": "deadbeef",
                        "size_bytes": 6,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    r = verify_artifact_checksums(exp_dir)
    assert r["trace.csv"]["status"] == "SECURITY_VIOLATION"
    # outside file must not be hashed/read as verified content in result
    assert r["trace.csv"].get("current_sha256") != _sha256_bytes(b"secret")


def test_atomic_write_failure_resilience(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = tmp_path / "exp_atomic"
    exp_dir.mkdir()
    original = {"experiment_id": "exp_atomic", "status": "RUNNING", "keep": "original"}
    (exp_dir / "manifest.json").write_text(json.dumps(original), encoding="utf-8")

    import manet.adapters.workspace as ws

    def boom(src: object, dst: object) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(ws.os, "replace", boom)
    with pytest.raises(OSError, match="simulated replace failure"):
        update_manifest_status(exp_dir, "COMPLETED")
    still = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
    assert still == original


def test_failed_and_interrupted_run_partial_artifacts(tmp_path: Path) -> None:
    for status in ("FAILED", "INTERRUPTED"):
        exp_dir = tmp_path / f"exp_{status.lower()}"
        exp_dir.mkdir()
        (exp_dir / "trace.csv").write_text("h\na\n", encoding="utf-8")
        (exp_dir / "manifest.json").write_text(
            json.dumps({"experiment_id": exp_dir.name, "status": "RUNNING"}), encoding="utf-8"
        )
        update_manifest_status(exp_dir, status, error="boom" if status == "FAILED" else None)
        m = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
        assert m["status"] == status
        assert "artifacts" in m
        assert "trace.csv" in m["artifacts"]
        assert m["artifacts"]["trace.csv"]["sha256"]


def test_manifest_tag_recording_and_summary_parsing(tmp_path: Path) -> None:
    ws_root = tmp_path / "ws"
    ws_root.mkdir()
    exp_dir = ws_root / "exp_20240101_120000_scenario_1_mytag"
    exp_dir.mkdir()
    record_launch_manifest(
        exp_dir, exp_dir.name, "scenario", 1, {"duration": 10}, tag="mytag"
    )
    m = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
    assert m["tag"] == "mytag"

    # missing tag in manifest, legacy parse from dir name
    exp2 = ws_root / "exp_20240102_120000_scenario_2_legacytag"
    exp2.mkdir()
    (exp2 / "manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": exp2.name,
                "scenario_name": "scenario",
                "seed": 2,
                "status": "COMPLETED",
                "created_at": "",
            }
        ),
        encoding="utf-8",
    )
    # empty tag
    exp3 = ws_root / "exp_20240103_120000_scenario_3"
    exp3.mkdir()
    (exp3 / "manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": exp3.name,
                "scenario_name": "scenario",
                "seed": 3,
                "status": "COMPLETED",
                "created_at": "",
                "tag": "",
            }
        ),
        encoding="utf-8",
    )
    adapter = WorkspaceAdapter(workspace_root=ws_root)
    runs = adapter.list_recent_experiments(limit=None)
    by_id = {r.experiment_id: r for r in runs}
    assert by_id[exp_dir.name].tag == "mytag"
    assert by_id[exp2.name].tag == "legacytag"
    assert by_id[exp3.name].tag is None


def test_tag_extraction_with_underscored_scenario_name(tmp_path: Path) -> None:
    ws_root = tmp_path / "ws"
    ws_root.mkdir()
    # blackhole_attack scenario, seed 42, tag eval
    exp_dir = ws_root / "exp_20240101_120000_blackhole_attack_42_eval"
    exp_dir.mkdir()
    (exp_dir / "manifest.json").write_text(
        json.dumps(
            {
                "experiment_id": exp_dir.name,
                "scenario_name": "blackhole_attack",
                "seed": 42,
                "status": "COMPLETED",
                "created_at": "",
            }
        ),
        encoding="utf-8",
    )
    adapter = WorkspaceAdapter(workspace_root=ws_root)
    runs = adapter.list_recent_experiments(limit=None)
    assert len(runs) == 1
    assert runs[0].tag == "eval"
    assert runs[0].scenario_name == "blackhole_attack"
    assert runs[0].seed == 42
