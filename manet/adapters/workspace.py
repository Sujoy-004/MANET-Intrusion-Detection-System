"""Workspace adapter providing read-only inspection of .manet-workspace/ experiments."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


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
    """Strictly read-only adapter discovering experiment runs in .manet-workspace/."""

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


__all__ = ["ExperimentSummary", "WorkspaceAdapter"]
