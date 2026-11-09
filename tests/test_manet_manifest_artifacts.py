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
