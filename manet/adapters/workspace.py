"""Workspace adapter providing inspection and experiment directory allocation under .manet-workspace/."""

from __future__ import annotations

from dataclasses import dataclass
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
from typing import Any

import manet
from manet.runtime.paths import get_project_root


ARTIFACT_FILENAMES = ("trace.csv", "isolation_log.csv", "isolation_log.json")


def sanitize_run_tag(tag: str) -> str:
    """Sanitize user-supplied run tag to prevent directory traversal and Windows-illegal filenames.

    Strips path traversal dots, spaces, symbols, and Windows-illegal path characters (\\ / : * ? " < > |).
    Leading/trailing underscores and dots are stripped both before and after truncation to 32 characters.
    """
    if not tag:
        return ""
    cleaned = tag.strip()
    # Replace directory traversal dots (.. or more) with underscore
    cleaned = re.sub(r"\.\.+", "_", cleaned)
    # Replace spaces, slashes, colons, and Windows-illegal characters
    cleaned = re.sub(r'[\s\\/:*?"<>|]+', "_", cleaned)
    # Strip leading/trailing dots and underscores both before and after truncation
    cleaned = cleaned.strip("._")
    return cleaned[:32].rstrip("._")


def _extract_legacy_tag(experiment_id: str, scenario_name: str | None, seed: Any) -> str | None:
    """Extract tag from legacy experiment directory name."""
    m = re.match(
        r"^exp_\d{8}_\d{6}_(?P<scenario>.+?)_(?P<seed>\d+)(?:_(?P<tag>.+))?$",
        experiment_id,
    )
    if m:
        tag = m.group("tag")
        if tag:
            return tag
    if scenario_name is not None and seed is not None:
        try:
            seed_i = int(seed)
        except (TypeError, ValueError):
            return None
        clean_scenario = re.sub(r'[\s\\/:*?"<>|]+', "_", str(scenario_name).strip()).strip("._") or "scenario"
        m2 = re.match(
            rf"^exp_\d{{8}}_\d{{6}}_{re.escape(clean_scenario)}_{seed_i}_(.+)$",
            experiment_id,
        )
        if m2:
            return m2.group(1)
    return None


def _compute_file_hash_and_rows(file_path: Path) -> tuple[str, int, int | None]:
    """Compute SHA-256 (64KB chunks), byte size, and type-aware row/record count."""
    hasher = hashlib.sha256()
    size_bytes = 0
    total_lines = 0
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
            size_bytes += len(chunk)
            total_lines += chunk.count(b"\n")
    row_count: int | None
    if file_path.suffix.lower() == ".csv":
        row_count = max(0, total_lines - 1) if total_lines > 0 else 0
    elif file_path.suffix.lower() == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                row_count = len(data)
            else:
                row_count = None
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            row_count = None
    else:
        row_count = total_lines
    return hasher.hexdigest(), size_bytes, row_count


def compute_experiment_artifacts(experiment_dir: Path) -> dict[str, dict[str, Any]]:
    """Compute artifact hashes, sizes, and row counts for generated payload files."""
    artifacts: dict[str, dict[str, Any]] = {}
    for filename in ARTIFACT_FILENAMES:
        file_path = experiment_dir / filename
        if file_path.is_file():
            sha256, size_bytes, row_count = _compute_file_hash_and_rows(file_path)
            artifacts[filename] = {
                "filename": filename,
                "relative_path": filename,
                "size_bytes": size_bytes,
                "sha256": sha256,
                "row_count": row_count,
            }
    return artifacts


def record_launch_manifest(
    experiment_dir: Path,
    experiment_id: str,
    scenario_name: str,
    seed: int,
    config: dict[str, Any],
    tag: str | None = None,
) -> Path:
    """Record initial launch manifest for an experiment run."""
    manifest_path = experiment_dir / "manifest.json"
    raw_tag = tag if tag is not None else (config.get("tag") if isinstance(config, dict) else None)
    clean_tag = sanitize_run_tag(str(raw_tag)) if raw_tag else ""
    manifest_data = {
        "experiment_id": experiment_id,
        "scenario_name": scenario_name,
        "seed": int(seed),
        "status": "CONFIGURED",
        "software_version": getattr(manet, "__version__", "2.0.0-dev"),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "trace_path": str(experiment_dir / "trace.csv"),
        "configuration": config,
        "tag": clean_tag or None,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    return manifest_path


def update_manifest_status(
    experiment_dir: Path,
    status: str,
    metrics: dict[str, float] | None = None,
    error: str | None = None,
) -> Path:
    """Atomically update status, metrics, timestamps, and terminal artifacts in manifest.json."""
    manifest_path = experiment_dir / "manifest.json"
    tmp_path = experiment_dir / "manifest.json.tmp"

    if manifest_path.is_file():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    else:
        manifest_data = {
            "experiment_id": experiment_dir.name,
            "scenario_name": "Unknown",
            "seed": 0,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest_data["status"] = status
    manifest_data["updated_at"] = now_iso

    if status == "RUNNING":
        if not manifest_data.get("started_at"):
            manifest_data["started_at"] = now_iso

    if status in ("COMPLETED", "INTERRUPTED", "FAILED"):
        manifest_data["completed_at"] = now_iso
        manifest_data["artifacts"] = compute_experiment_artifacts(experiment_dir)

    if metrics is not None:
        manifest_data["metrics"] = metrics
        if "pdr" in metrics and metrics["pdr"] is not None:
            manifest_data["pdr"] = metrics["pdr"]

    if error is not None:
        manifest_data["error_details"] = str(error)

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    os.replace(tmp_path, manifest_path)
    return manifest_path


def get_experiment_manifest(
    experiment_dir_or_id: Path | str,
    workspace_root: Path | None = None,
) -> dict[str, Any] | None:
    """Load full experiment manifest, or None if missing/invalid."""
    if isinstance(experiment_dir_or_id, Path):
        experiment_dir = experiment_dir_or_id
    else:
        root = workspace_root or (get_project_root() / ".manet-workspace")
        experiment_dir = root / str(experiment_dir_or_id)
    manifest_path = experiment_dir / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def verify_artifact_checksums(
    experiment_dir: Path,
    workspace_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Verify recorded artifact checksums on demand against files on disk."""
    del workspace_root
    manifest = get_experiment_manifest(experiment_dir)
    if manifest is None:
        return {}
    exp_resolved = experiment_dir.resolve()
    recorded = manifest.get("artifacts")
    if not isinstance(recorded, dict) or not recorded:
        # Legacy: inspect known artifacts and report RECORDED
        results: dict[str, dict[str, Any]] = {}
        for filename in ARTIFACT_FILENAMES:
            file_path = experiment_dir / filename
            if file_path.is_file():
                try:
                    sha256, size_bytes, row_count = _compute_file_hash_and_rows(file_path)
                    results[filename] = {
                        "status": "RECORDED",
                        "expected_sha256": None,
                        "current_sha256": sha256,
                        "size_bytes": size_bytes,
                        "row_count": row_count,
                    }
                except (OSError, PermissionError) as exc:
                    results[filename] = {
                        "status": "ERROR",
                        "expected_sha256": None,
                        "current_sha256": None,
                        "error": str(exc),
                    }
        return results

    results = {}
    for filename, info in recorded.items():
        if not isinstance(info, dict):
            continue
        rel_path = str(info.get("relative_path") or info.get("filename") or filename)
        try:
            target_file = (experiment_dir / rel_path).resolve()
        except (OSError, ValueError) as exc:
            results[filename] = {
                "status": "ERROR",
                "expected_sha256": info.get("sha256"),
                "current_sha256": None,
                "error": str(exc),
            }
            continue
        try:
            if not target_file.is_relative_to(exp_resolved):
                results[filename] = {
                    "status": "SECURITY_VIOLATION",
                    "expected_sha256": info.get("sha256"),
                    "current_sha256": None,
                    "error": "Artifact path escapes experiment directory",
                }
                continue
        except (OSError, ValueError):
            results[filename] = {
                "status": "SECURITY_VIOLATION",
                "expected_sha256": info.get("sha256"),
                "current_sha256": None,
                "error": "Artifact path escapes experiment directory",
            }
            continue

        if not target_file.exists() or not target_file.is_file():
            results[filename] = {
                "status": "MISSING",
                "expected_sha256": info.get("sha256"),
                "current_sha256": None,
                "size_bytes": info.get("size_bytes"),
                "row_count": info.get("row_count"),
            }
            continue
        try:
            current_sha256, size_bytes, row_count = _compute_file_hash_and_rows(target_file)
        except (OSError, PermissionError) as exc:
            results[filename] = {
                "status": "ERROR",
                "expected_sha256": info.get("sha256"),
                "current_sha256": None,
                "error": str(exc),
            }
            continue
        expected = info.get("sha256")
        status = "VERIFIED" if expected == current_sha256 else "CORRUPTED"
        results[filename] = {
            "status": status,
            "expected_sha256": expected,
            "current_sha256": current_sha256,
            "size_bytes": size_bytes,
            "row_count": row_count,
        }
    return results


@dataclass(frozen=True)
class ExperimentSummary:
    """Summary of a past experiment run discovered in the workspace."""

    experiment_id: str
    scenario_name: str
    seed: int
    status: str
    created_at: str
    pdr: float | None = None
    tag: str | None = None


class WorkspaceAdapter:
    """Workspace adapter discovering past runs and allocating collision-free experiment directories."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or (get_project_root() / ".manet-workspace")

    def has_experiments(self) -> bool:
        """Check if any experiment records exist in the workspace."""
        return len(self.list_recent_experiments(limit=1)) > 0

    def _summary_from_manifest(self, data: dict[str, Any], fallback_id: str) -> ExperimentSummary:
        tag = data.get("tag")
        if tag is not None and str(tag).strip() == "":
            tag = None
        if tag is None:
            tag = _extract_legacy_tag(
                str(data.get("experiment_id", fallback_id)),
                data.get("scenario_name"),
                data.get("seed"),
            )
        return ExperimentSummary(
            experiment_id=data.get("experiment_id", fallback_id),
            scenario_name=data.get("scenario_name", "Unknown"),
            seed=int(data.get("seed", 0)),
            status=data.get("status", "COMPLETED"),
            created_at=str(data.get("created_at", "")),
            pdr=float(data["pdr"]) if "pdr" in data and data["pdr"] is not None else None,
            tag=str(tag) if tag is not None else None,
        )

    def list_recent_experiments(self, limit: int | None = 20) -> list[ExperimentSummary]:
        """Discover and list recent experiment runs (strictly read-only). limit=None returns all."""
        if not self.workspace_root.is_dir():
            return []

        runs: list[ExperimentSummary] = []
        try:
            entries = sorted(
                [d for d in self.workspace_root.iterdir()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        except (OSError, ValueError):
            return []

        for entry in entries:
            if entry.is_dir():
                manifest_file = entry / "manifest.json"
                summary_file = entry / "run_summary.json"
                meta_file = (
                    manifest_file
                    if manifest_file.is_file()
                    else (summary_file if summary_file.is_file() else None)
                )

                if meta_file:
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, dict):
                            runs.append(self._summary_from_manifest(data, entry.name))
                    except (json.JSONDecodeError, OSError, ValueError, KeyError):
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
                            tag=_extract_legacy_tag(entry.name, entry.name, 0),
                        )
                    )
            elif entry.is_file() and entry.suffix == ".json":
                try:
                    with open(entry, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        runs.append(self._summary_from_manifest(data, entry.stem))
                except (json.JSONDecodeError, OSError, ValueError, KeyError):
                    continue

            if limit is not None and len(runs) >= limit:
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
        clean_scenario = (
            re.sub(r'[\s\\/:*?"<>|]+', "_", scenario_name.strip()).strip("._") or "scenario"
        )
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
                raise ValueError(
                    f"Allocated experiment path {exp_dir} escapes workspace root {self.workspace_root}"
                )

            try:
                exp_dir.mkdir(parents=True, exist_ok=False)
                return candidate_id, exp_dir
            except FileExistsError:
                candidate_id = f"{base_id}_{counter}"
                exp_dir = self.workspace_root / candidate_id
                counter += 1


    def _resolve_experiment_dir(self, experiment_id: str) -> Path:
        candidate_raw = self.workspace_root / experiment_id
        if os.path.islink(candidate_raw):
            raise ValueError(f"Symlinked experiment directory is prohibited: {experiment_id}")
        target_dir = candidate_raw.resolve()
        root_resolved = self.workspace_root.resolve()
        if not target_dir.is_relative_to(root_resolved) or target_dir == root_resolved:
            raise ValueError(f"Invalid experiment directory traversal attempt: {experiment_id}")
        if not target_dir.is_dir():
            raise FileNotFoundError(f"Experiment directory not found: {experiment_id}")
        return target_dir

    def preview_experiment_deletion(self, experiment_id: str) -> dict[str, Any]:
        """Recursively enumerate experiment files with cryptographic fingerprint for safe deletion."""
        target_dir = self._resolve_experiment_dir(experiment_id)
        files: list[dict[str, Any]] = []
        for root_dir, dirs, filenames in os.walk(target_dir, followlinks=False):
            root_path = Path(root_dir)
            for d in dirs:
                dir_path = root_path / d
                if os.path.islink(dir_path):
                    raise ValueError(
                        f"Symlinked directory inside experiment directory is prohibited: {dir_path}"
                    )
            for fname in filenames:
                file_path = root_path / fname
                if os.path.islink(file_path):
                    raise ValueError(
                        f"Symlinked file inside experiment directory is prohibited: {file_path}"
                    )
                st = os.lstat(file_path)
                sha256, _, _ = _compute_file_hash_and_rows(file_path)
                rel = file_path.relative_to(target_dir).as_posix()
                files.append(
                    {
                        "relative_path": rel,
                        "size_bytes": int(st.st_size),
                        "mtime_ns": int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))),
                        "content_sha256": sha256,
                        "name": rel,
                    }
                )
        files_sorted = sorted(files, key=lambda f: f["relative_path"])
        fp_material = "\n".join(
            f"{f['relative_path']}:{f['size_bytes']}:{f['mtime_ns']}:{f['content_sha256']}"
            for f in files_sorted
        )
        fingerprint = hashlib.sha256(fp_material.encode("utf-8")).hexdigest()
        total_bytes = sum(f["size_bytes"] for f in files_sorted)
        return {
            "experiment_id": experiment_id,
            "path": str(target_dir),
            "files": files_sorted,
            "total_bytes": total_bytes,
            "file_count": len(files_sorted),
            "fingerprint": fingerprint,
        }

    def delete_experiment_run(
        self, experiment_id: str, expected_preview: dict[str, Any] | None = None
    ) -> int:
        """Delete experiment directory after optional cryptographic revalidation."""
        target_dir = self._resolve_experiment_dir(experiment_id)
        if expected_preview is not None:
            fresh = self.preview_experiment_deletion(experiment_id)
            if fresh["fingerprint"] != expected_preview["fingerprint"]:
                raise RuntimeError(
                    "Experiment contents modified since deletion preview was generated. Aborting deletion."
                )
            total_bytes = int(fresh["total_bytes"])
        else:
            # compute for return value
            try:
                fresh = self.preview_experiment_deletion(experiment_id)
                total_bytes = int(fresh["total_bytes"])
            except Exception:
                total_bytes = 0
        # Atomic deletion:
        # Instead of calling shutil.rmtree directly on target_dir (which deletes files
        # sequentially and can leave an experiment half-deleted if a file like trace.csv
        # is locked by another Windows process), atomically rename target_dir to a staging
        # trash directory first.
        #
        # 1. On Windows, if any file inside target_dir is held open without FILE_SHARE_DELETE
        #    (such as in Excel or a viewer), the rename of target_dir fails immediately with
        #    PermissionError/OSError.
        # 2. Because failure occurs on the directory rename, ZERO files inside target_dir are
        #    deleted or modified — manifest.json and all artifacts remain completely intact.
        # 3. Only once safely renamed is shutil.rmtree executed on the trash directory.
        # 4. If rmtree fails unexpectedly after rename, rollback by renaming trash_dir back
        #    to target_dir is attempted before raising.
        trash_dir = target_dir.parent / f".deleting_{target_dir.name}_{time.time_ns()}"
        try:
            target_dir.rename(trash_dir)
        except PermissionError as exc:
            raise RuntimeError(
                f"Cannot delete experiment run '{experiment_id}': files are locked by another Windows process. Please close any open handles."
            ) from exc
        except OSError as exc:
            raise RuntimeError(str(exc)) from exc

        try:
            shutil.rmtree(trash_dir)
        except PermissionError as exc:
            if trash_dir.exists() and not target_dir.exists():
                try:
                    trash_dir.rename(target_dir)
                except Exception:
                    pass
            raise RuntimeError(
                f"Cannot delete experiment run '{experiment_id}': files are locked by another Windows process. Please close any open handles."
            ) from exc
        except OSError as exc:
            if trash_dir.exists() and not target_dir.exists():
                try:
                    trash_dir.rename(target_dir)
                except Exception:
                    pass
            raise RuntimeError(str(exc)) from exc
        return total_bytes

    compute_experiment_artifacts = staticmethod(compute_experiment_artifacts)
    verify_artifact_checksums = staticmethod(verify_artifact_checksums)
    get_experiment_manifest = staticmethod(get_experiment_manifest)
    record_launch_manifest = staticmethod(record_launch_manifest)
    update_manifest_status = staticmethod(update_manifest_status)


__all__ = [
    "ExperimentSummary",
    "WorkspaceAdapter",
    "compute_experiment_artifacts",
    "get_experiment_manifest",
    "record_launch_manifest",
    "sanitize_run_tag",
    "update_manifest_status",
    "verify_artifact_checksums",
]
