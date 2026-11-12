"""External composition root injecting concrete simulation execution into ManetApp.

Preserves strict architectural package isolation:
- manet/ modules never import business logic (simulator, attacks, feature_extraction, ml).
- simulator/ modules never import manet.
This module lives at the repository root and binds ConcreteSimulationExecutor to
ManetApp at startup.
"""

from __future__ import annotations

import copy
from pathlib import Path
import threading
from typing import Any, Callable, Dict, Optional

from simpy.core import EmptySchedule, StopSimulation
from simpy.events import Event, URGENT

from manet.adapters.execution import TelemetryEvent
from manet.adapters.handoff import SimulationLaunchRequest
from manet.app import ManetApp
from manet.runtime.paths import get_project_root
from simulator.metrics import compute_metrics
from simulator.run_scenario import SimulationRunner


class ConcreteSimulationExecutor:
    """Concrete stepping executor implementing SimulationExecutorProtocol."""

    def execute_simulation(
        self,
        launch_request: SimulationLaunchRequest,
        cancel_token: threading.Event,
        telemetry_sink: Any,
        stage_cb: Callable[[str], None],
        progress_cb: Callable[[float, float], None],
    ) -> Dict[str, float]:
        """Execute simulation discrete-event stepping loop and return computed metrics."""
        stage_cb("INITIALIZING")
        cfg = copy.deepcopy(launch_request.config)

        # IDS model path resolution and isolation log configuration
        if cfg.get("ids", {}).get("enabled", False):
            ids_cfg = cfg["ids"]
            raw_model_path = ids_cfg.get("model_path", "ml/models/best_model.joblib")
            model_p = Path(raw_model_path)
            if not model_p.is_absolute():
                model_p = (get_project_root() / model_p).resolve()
            ids_cfg["model_path"] = str(model_p)
            ids_cfg["isolation_log_path"] = str(launch_request.workspace_dir / "isolation_log.json")

        launch_request.workspace_dir.mkdir(parents=True, exist_ok=True)
        out_trace_path = launch_request.workspace_dir / "trace.csv"

        runner = SimulationRunner(
            scenario_config=cfg,
            seed=launch_request.seed,
            out_path=out_trace_path,
        )

        # Hook log_event to pipe telemetry events into telemetry_sink
        original_log_event = runner.log_event

        def hooked_log_event(
            sim_time: float,
            src: int,
            dst: int,
            pkt_id: int,
            pkt_type: str,
            hop_count: int,
            dropped_by: Optional[int] = None,
            node_id: Optional[int] = None,
            speed: Optional[float] = None,
            neighbor_count: Optional[int] = None,
        ) -> None:
            original_log_event(
                sim_time=sim_time,
                src=src,
                dst=dst,
                pkt_id=pkt_id,
                pkt_type=pkt_type,
                hop_count=hop_count,
                dropped_by=dropped_by,
                node_id=node_id,
                speed=speed,
                neighbor_count=neighbor_count,
            )
            if telemetry_sink is not None:
                acting_node = node_id if node_id is not None else src
                dropped_str = str(dropped_by) if dropped_by is not None else ""
                speed_str = f"{speed:.4f}" if speed is not None else ""
                nbr_str = str(neighbor_count) if neighbor_count is not None else ""
                te = TelemetryEvent(
                    sim_time=float(sim_time),
                    src=int(src),
                    dst=int(dst),
                    pkt_id=int(pkt_id),
                    pkt_type=str(pkt_type),
                    hop_count=int(hop_count) if hop_count is not None else 0,
                    dropped_by=dropped_str,
                    node_id=int(acting_node),
                    speed=speed_str,
                    neighbor_count=nbr_str,
                )
                telemetry_sink.record_event(te)

        runner.log_event = hooked_log_event

        step_count = 0
        try:
            runner.initialize_nodes()
            runner.initialize_traffic()

            stage_cb("SIMULATING")
            progress_cb(0.0, runner.duration)

            # Schedule URGENT until event at duration to guarantee clean boundary completion
            until = Event(runner.env)
            until._ok = True
            until._value = None
            runner.env.schedule(until, URGENT, max(0.0, runner.duration - runner.env.now))
            until.callbacks.append(StopSimulation.callback)

            while True:
                if cancel_token.is_set():
                    break
                runner.env.step()
                step_count += 1
                if step_count % 200 == 0:
                    progress_cb(runner.env.now, runner.duration)
        except StopSimulation:
            pass
        except EmptySchedule:
            pass
        except Exception as exc:
            # Robust best-effort finalization on execution failure (initialization or stepping)
            finalization_err = None
            try:
                runner.write_traces()
                if runner.online_ids is not None and runner.online_ids.isolation_log_path is not None:
                    runner.online_ids.write_isolation_log()
            except Exception as f_err:
                finalization_err = f_err

            if finalization_err is not None:
                raise RuntimeError(
                    f"Simulation execution failed: {exc}; secondary finalization error: {finalization_err}"
                ) from exc
            raise exc

        # Finalize normal completion or cooperative interruption
        progress_cb(runner.env.now, runner.duration)
        stage_cb("FINALIZING")

        runner.write_traces()
        if runner.online_ids is not None and runner.online_ids.isolation_log_path is not None:
            runner.online_ids.write_isolation_log()

        metrics = compute_metrics(runner.trace_rows, sim_duration=runner.duration)
        return metrics


def ensure_champion_model(project_root: Optional[Path] = None) -> None:
    """Ensure the champion model exists on disk, training and evaluating if missing."""
    root = (project_root or get_project_root()).resolve()
    model_path = root / "ml" / "models" / "best_model.joblib"
    if model_path.is_file() and model_path.stat().st_size > 0:
        return

    import sys
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    train_csv = root / "data" / "train.csv"
    if not (train_csv.is_file() and train_csv.stat().st_size > 0):
        from scripts.build_dataset import main as build_dataset_main
        build_dataset_main(["--multi-attack"])

    from ml.train import tune_and_save
    tune_and_save(train_path=str(train_csv), models_dir=str(root / "ml" / "models"))

    from ml.evaluate import main as evaluate_main
    evaluate_main()


def create_app(auto_bootstrap: bool = True, **kwargs: Any) -> ManetApp:
    """Instantiate ManetApp injected with ConcreteSimulationExecutor."""
    if auto_bootstrap:
        ensure_champion_model()
    executor = ConcreteSimulationExecutor()
    return ManetApp(executor=executor, **kwargs)


__all__ = [
    "ConcreteSimulationExecutor",
    "create_app",
    "ensure_champion_model",
]
