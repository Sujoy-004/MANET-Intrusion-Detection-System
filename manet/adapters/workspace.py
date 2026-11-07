"""Workspace adapter providing inspection and experiment directory allocation under .manet-workspace/."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import json
from pathlib import Path
import re
from typing import Any

import manet


def sanitize_run_tag(tag: str) -> str:
    """Sanitize user-supplied run tag to prevent directory traversal and Windows-illegal filenames.

    Strips path traversal dots, spaces, symbols, and Windows-illegal path characters (\\ / : * ? " < > |).
    Leading/trailing underscores and dots are stripped, and the result is truncated to 32 characters.
    """
    if not tag:
        return ""
    cleaned = tag.strip()
    # Replace directory traversal dots (.. or more) with underscore
    cleaned = re.sub(r"\.\.+", "_", cleaned)
    # Replace spaces, slashes, colons, and Windows-illegal characters
    cleaned = re.sub(r'[\s\\/:*?"<>|]+', "_", cleaned)
    # Strip leading/trailing dots and underscores
    cleaned = cleaned.strip("._")
    return cleaned[:32]


def record_launch_manifest(
    experiment_dir: Path,
    experiment_id: str,
    scenario_name: str,
    seed: int,
    config: dict[str, Any],
) -> Path:
    """Record initial launch manifest for an experiment run."""
    manifest_path = experiment_dir / "manifest.json"
    manifest_data = {
        "experiment_id": experiment_id,
        "scenario_name": scenario_name,
        "seed": int(seed),
        "status": "CONFIGURED",
        "software_version": getattr(manet, "__version__", "2.0.0-dev"),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "trace_path": str(experiment_dir / "trace.csv"),
        "configuration": config,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    return manifest_path


@dataclass(frozen=True)
class ExperimentSummary:
    """Summary of a past experiment run discovered in the workspace."""

    experiment_id: str
    scenario_name: str
    seed: int
    status: str
    created_at: str
    pdr: float | None = None


class WorkspaceAdapter:
    """Workspace adapter discovering past runs and allocating collision-free experiment directories."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or (Path.cwd() / ".manet-workspace")

    def has_experiments(self) -> bool:
        """Check if any experiment records exist in the workspace."""
        return len(self.list_recent_experiments(limit=1)) > 0

    def list_recent_experiments(self, limit: int = 5) -> list[ExperimentSummary]:
        """Discover and list recent experiment runs up to limit (strictly read-only)."""
        if not self.workspace_root.is_dir():
            return []

        runs: list[ExperimentSummary] = []
        try:
            entries = sorted(
                [d for d in self.workspace_root.iterdir()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        except Exception:
            return []

        for entry in entries:
            if entry.is_dir():
                manifest_file = entry / "manifest.json"
                summary_file = entry / "run_summary.json"
                meta_file = manifest_file if manifest_file.is_file() else (summary_file if summary_file.is_file() else None)

                if meta_file:
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, dict):
                            runs.append(
                                ExperimentSummary(
                                    experiment_id=data.get("experiment_id", entry.name),
                                    scenario_name=data.get("scenario_name", "Unknown"),
                                    seed=int(data.get("seed", 0)),
                                    status=data.get("status", "COMPLETED"),
                                    created_at=str(data.get("created_at", "")),
                                    pdr=float(data["pdr"]) if "pdr" in data and data["pdr"] is not None else None,
                                )
                            )
                    except Exception:
                        continue
                else:
                    runs.append(
                        ExperimentSummary(
                            experiment_id=entry.name,
                            scenario_name=entry.name,
                            seed=0,
                            status="UNKNOWN",
                            created_at="",
                            pdr=None,
                        )
                    )
            elif entry.is_file() and entry.suffix == ".json":
                try:
                    with open(entry, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        runs.append(
                            ExperimentSummary(
                                experiment_id=data.get("experiment_id", entry.stem),
                                scenario_name=data.get("scenario_name", entry.stem),
                                seed=int(data.get("seed", 0)),
                                status=data.get("status", "COMPLETED"),
                                created_at=str(data.get("created_at", "")),
                                pdr=float(data["pdr"]) if "pdr" in data and data["pdr"] is not None else None,
                            )
                        )
                except Exception:
                    continue

            if len(runs) >= limit:
                break

        return runs

    def allocate_experiment_directory(
        self,
        scenario_name: str,
        seed: int,
        tag: str | None = None,
    ) -> tuple[str, Path]:
        """Allocate a unique, collision-free experiment directory under workspace_root.

        Format: exp_YYYYMMDD_HHMMSS_<scenario_name>_<seed>[_<sanitized_tag>]
        Appends _1, _2, etc. if directory exists.
        """
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        clean_scenario = re.sub(r'[\s\\/:*?"<>|]+', "_", scenario_name.strip()).strip("._") or "scenario"
        base_id = f"exp_{now_str}_{clean_scenario}_{seed}"
        if tag:
            clean_tag = sanitize_run_tag(tag)
            if clean_tag:
                base_id = f"{base_id}_{clean_tag}"

        self.workspace_root.mkdir(parents=True, exist_ok=True)
        root_resolved = self.workspace_root.resolve()

        candidate_id = base_id
        exp_dir = self.workspace_root / candidate_id
        counter = 1

        while True:
            resolved = exp_dir.resolve()
            if not resolved.is_relative_to(root_resolved):
                raise ValueError(f"Allocated experiment path {exp_dir} escapes workspace root {self.workspace_root}")

            try:
                exp_dir.mkdir(parents=True, exist_ok=False)
                return candidate_id, exp_dir
            except FileExistsError:
                candidate_id = f"{base_id}_{counter}"
                exp_dir = self.workspace_root / candidate_id
                counter += 1

    record_launch_manifest = staticmethod(record_launch_manifest)


__all__ = [
    "ExperimentSummary",
    "WorkspaceAdapter",
    "record_launch_manifest",
    "sanitize_run_tag",
]
