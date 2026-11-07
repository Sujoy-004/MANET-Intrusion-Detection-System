"""Runtime diagnostics probe inspecting environment and artifacts with zero mock values."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_PACKAGES: tuple[str, ...] = (
    "simpy",
    "networkx",
    "sklearn",
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "pytest",
    "joblib",
)

DISTRIBUTION_MAPPING: dict[str, str] = {
    "sklearn": "scikit-learn",
}


@dataclass(frozen=True)
class CapabilityStatus:
    """Status record for a component or artifact capability."""

    name: str
    state: str  # "VERIFIED", "PARTIAL", "EXPERIMENTAL", "UNAVAILABLE"
    details: str
    remediation: str | None = None


@dataclass(frozen=True)
class DiagnosticsReport:
    """Comprehensive system capability diagnostics report."""

    python_version: tuple[str, bool]
    dependencies: dict[str, tuple[bool, str]]
    scenarios: CapabilityStatus
    datasets: CapabilityStatus
    model_artifact: CapabilityStatus


class DiagnosticsProbe:
    """Probes runtime environment and filesystem artifacts with zero mock values."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def probe_python_version(self) -> tuple[str, bool]:
        """Probe runtime Python version and verified status (requires Python >= 3.11)."""
        version_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        is_verified = sys.version_info >= (3, 11)
        return version_str, is_verified

    def probe_dependencies(self) -> dict[str, tuple[bool, str]]:
        """Check presence and versions of required core packages without importing them."""
        results: dict[str, tuple[bool, str]] = {}
        for mod in REQUIRED_PACKAGES:
            dist = DISTRIBUTION_MAPPING.get(mod, mod)
            spec = importlib.util.find_spec(mod)
            available = spec is not None
            ver = "missing"
            if available:
                try:
                    ver = importlib.metadata.version(dist)
                except Exception:
                    ver = "installed"
            results[mod] = (available, ver)
        return results

    def probe_scenarios(self) -> CapabilityStatus:
        """Inspect scenarios/*.json files and validate preset structure."""
        scenarios_dir = self.repo_root / "scenarios"
        if not scenarios_dir.is_dir():
            return CapabilityStatus(
                name="Scenarios",
                state="UNAVAILABLE",
                details="scenarios/ directory not found",
                remediation="Restore scenario presets in scenarios/",
            )

        json_files = sorted(scenarios_dir.glob("*.json"))
        if not json_files:
            return CapabilityStatus(
                name="Scenarios",
                state="UNAVAILABLE",
                details="No scenario files found in scenarios/",
                remediation="Restore scenario presets in scenarios/",
            )

        valid_count = 0
        malformed_files: list[str] = []

        for fpath in json_files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and ("scenario_id" in data or "nodes" in data):
                    valid_count += 1
                else:
                    malformed_files.append(fpath.name)
            except Exception:
                malformed_files.append(fpath.name)

        if valid_count == 0:
            return CapabilityStatus(
                name="Scenarios",
                state="UNAVAILABLE",
                details=f"No valid presets found ({len(malformed_files)} malformed files)",
                remediation="Restore valid scenario JSON files to scenarios/",
            )

        details = f"{valid_count} valid presets available"
        if malformed_files:
            details += f" ({len(malformed_files)} malformed: {', '.join(malformed_files)})"

        return CapabilityStatus(
            name="Scenarios",
            state="VERIFIED",
            details=details,
            remediation=None,
        )

    def probe_datasets(self) -> CapabilityStatus:
        """Inspect data/train.csv and data/test.csv via stat() with zero mock rows."""
        train_csv = self.repo_root / "data" / "train.csv"
        test_csv = self.repo_root / "data" / "test.csv"

        train_exists = train_csv.is_file()
        test_exists = test_csv.is_file()

        if train_exists and test_exists:
            try:
                train_size = train_csv.stat().st_size
                test_size = test_csv.stat().st_size
                return CapabilityStatus(
                    name="Datasets",
                    state="VERIFIED",
                    details=f"train.csv ({train_size} bytes), test.csv ({test_size} bytes)",
                    remediation=None,
                )
            except Exception as e:
                return CapabilityStatus(
                    name="Datasets",
                    state="EXPERIMENTAL",
                    details=f"Dataset stat error: {e}",
                    remediation="Verify filesystem permissions on data/",
                )

        missing: list[str] = []
        if not train_exists:
            missing.append("data/train.csv")
        if not test_exists:
            missing.append("data/test.csv")

        return CapabilityStatus(
            name="Datasets",
            state="UNAVAILABLE",
            details=f"Missing: {', '.join(missing)}",
            remediation="Run python scripts/build_dataset.py --multi-attack",
        )

    def probe_model_artifact(self) -> CapabilityStatus:
        """Inspect champion model artifact and metadata with dynamic provenance and honest Grayhole F1."""
        joblib_path = self.repo_root / "ml" / "models" / "best_model.joblib"
        metadata_path = self.repo_root / "ml" / "models" / "model_metadata.json"

        # Check binary existence first
        if not joblib_path.is_file():
            meta_note = " (historical metadata available)" if metadata_path.is_file() else ""
            return CapabilityStatus(
                name="Champion Model",
                state="UNAVAILABLE",
                details=f"Model binary not found: best_model.joblib missing{meta_note}",
                remediation="Run python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate",
            )

        if not metadata_path.is_file():
            return CapabilityStatus(
                name="Champion Model",
                state="UNAVAILABLE",
                details="Metadata missing/corrupt: model_metadata.json missing",
                remediation="Re-evaluate model: python -m ml.evaluate",
            )

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            if not isinstance(meta, dict):
                raise ValueError("model_metadata.json root must be a JSON object")

            champion = meta.get("champion", "model")
            metrics: dict[str, Any] | None = meta.get("test_metrics") or meta.get("metrics")
            if not isinstance(metrics, dict):
                raise KeyError("Missing 'test_metrics' or 'metrics' key in metadata")

            f1_bh = metrics.get("f1_blackhole")
            f1_gh = metrics.get("f1_grayhole")
            fpr = metrics.get("fpr")

            bh_str = f"BH F1: {f1_bh:.4f}" if isinstance(f1_bh, (int, float)) else "BH F1: N/A"
            fpr_str = f"FPR: {fpr:.4f}" if isinstance(fpr, (int, float)) else "FPR: N/A"

            # Honest Grayhole F1 evaluation: if 0.0, explicitly badge as ineffective
            if f1_gh == 0.0:
                gh_str = "PARTIAL (Grayhole F1: 0.0 - Ineffective Detection)"
                state = "PARTIAL"
                remediation = "Multi-attack tuning required for Grayhole detection"
            elif isinstance(f1_gh, (int, float)):
                gh_str = f"GH F1: {f1_gh:.4f}"
                state = "VERIFIED"
                remediation = None
            else:
                gh_str = "GH F1: N/A"
                state = "PARTIAL"
                remediation = "Model missing Grayhole evaluation metric"

            champion_name = champion.replace("_", " ").title() if isinstance(champion, str) else "Model"
            details = f"{champion_name} ({bh_str}, {gh_str}, {fpr_str})"

            return CapabilityStatus(
                name="Champion Model",
                state=state,
                details=details,
                remediation=remediation,
            )

        except (json.JSONDecodeError, KeyError, ValueError, Exception) as exc:
            return CapabilityStatus(
                name="Champion Model",
                state="UNAVAILABLE",
                details=f"Metadata missing/corrupt: {type(exc).__name__}",
                remediation="Re-evaluate model: python -m ml.evaluate",
            )

    def probe_all(self) -> DiagnosticsReport:
        """Run all diagnostic probes and return a unified DiagnosticsReport."""
        return DiagnosticsReport(
            python_version=self.probe_python_version(),
            dependencies=self.probe_dependencies(),
            scenarios=self.probe_scenarios(),
            datasets=self.probe_datasets(),
            model_artifact=self.probe_model_artifact(),
        )


__all__ = [
    "CapabilityStatus",
    "DiagnosticsProbe",
    "DiagnosticsReport",
    "REQUIRED_PACKAGES",
    "DISTRIBUTION_MAPPING",
]
