# AGENTS.md — MANET ML Intrusion Detection System

## Current state (read first)

This repo currently contains **only** `MANET_IDS_BTech_Execution_Guide.md` and this file.
There is no code, no manifest, no CI, and no test suite yet. Git is initialised on `main`
with **no remote configured** — everything stays local until a remote is deliberately added.

- `MANET_IDS_BTech_Execution_Guide.md` is the **project specification** (scope, phases,
  experiment matrix, feature schema, metrics, deliverables, viva questions). It has been
  revised to match the architecture below. Read it before planning work.
- `AGENTS.md` is the **binding engineering contract** — the rules distilled from the guide
  that agents break by default.
- **Precedence:** where the two conflict, `AGENTS.md` wins on engineering rules and the guide
  wins on project specification. **Keep both files in sync** — change one, change the other in
  the same commit. Never leave them disagreeing.

## Decisions in force (recorded in both files)

The guide originally assumed NS-3 + C++ on Ubuntu. It has been revised; these decisions are
now recorded in both files:

| Area | Decision |
|---|---|
| Language | **Python only** — simulator *and* ML. No C++ anywhere. |
| Simulator | **NS-3 is dropped.** Build an in-repo, pure-Python MANET simulator (see below). |
| Platform | **Windows-native.** No WSL, no Linux VM, no Docker, no C++ toolchain. |

Consequences to respect:
- Never attempt to install or build NS-3, `ns-3-dev`, or a C++ toolchain here. It will fail
  and it is out of scope.
- The guide has been revised, but you may encounter the original brief elsewhere (it reads
  like a mentor-supplied handbook). Where any copy still assumes NS-3, the in-repo
  `simulator/` package is the substitute. Keep the same pipeline shape:
  simulator → traces → features → dataset → ML → IDS response → network re-evaluation.
- The guide has been revised for this architecture. When you change the architecture again,
  update the guide in the same change — never leave the two files disagreeing.

## Recommended simulator: in-repo pure-Python MANET simulator

No installable Windows-native Python AODV simulator exists. Verified: no relevant package on
PyPI (`pymansim`, `manet`, `aodv`, `ns3`, … all absent) and GitHub search turns up only 0–1★
student repos. `ns.py` (PyPI, Apache-2.0, actively maintained) is a **wired IP-flow** simulator —
ports, schedulers, TCP/BBR, FatTree — with **no wireless, mobility, or AODV layer**, so it does
not cover the project's core needs. Building it in-repo is the pragmatic choice.

Stack (all pure Python, all Windows-safe):

- **SimPy 4.1.2** — discrete-event clock (`Environment`, `env.process`, `env.timeout`).
  Installed (pure Python, compiles nothing).
- **NetworkX 3.6.1** — topology graph, neighbor sets, route-graph analysis (already installed).
- stdlib `dataclasses` / `json` / `csv` for scenarios, traces, and metrics.

Suggested modules under `simulator/`, mirroring the guide's Module A:

- `mobility.py` — Random Waypoint; node speed = the `mobility_speed` feature.
- `radio.py` — transmission range / link availability; drives `neighbor_count`.
- `aodv.py` — RREQ/RREP/RERR, sequence numbers, route table with hop count and expiry.
  Must record `route_request_rate` / `route_reply_rate` per time window.
- `traffic.py` — CBR/UDP flows (source–dest pairs, packet rate, payload size).
- `attacks/` (top-level package, the guide's Module B) — Blackhole and Grayhole. Implement as
  **node behavior flags** on the AODV node: a lying reply (blackhole) and probabilistic drop
  (grayhole). This is far simpler than NS-3 hooks and is the main payoff of dropping NS-3.
- `metrics.py` — PDR, throughput, end-to-end delay, packet loss, routing overhead.
- `run_scenario.py` — CLI: `--scenario <json> --seed <int> --out <dir>`.

`simulator/` must **not** import `attacks/` directly. Attack behaviour is injected by the
scenario runner, so the simulator stays attack-agnostic and the same code produces the clean
baseline runs used as the IDS-off comparison.

Non-obvious requirements for the simulator:

- **Determinism:** every run is driven by an explicit integer seed. Same seed ⇒ identical
  traces. Otherwise "multiple seeds" in the experiment matrix is unreproducible.
- **Simulated time ≠ wall time.** Measured on this machine with a representative workload
  (mobility ticks, RREQ floods, hop-by-hop forwarding): 50 nodes / 8 flows / 10 pps /
  300 s simulated run with a blackhole attacker → **0.83 s wall**, ~70k events/sec. A
  30–60 s run takes well under a second, so the full experiment matrix is minutes of
  compute. If a run *is* slow, per-packet Python overhead is the culprit — profile before
  increasing node count.
- **Traces are CSV, one row per packet event** (`time, src, dst, pkt_id, type, hop_count,
  dropped_by, ...`), written to `traces/`. Features are derived from traces, never embedded
  in them.
- **Labels come from the scenario config** (which node is the attacker, which attack), never
  from the trace. This is what keeps the dataset ground truth honest — see leakage rule.
- Keep the attack's effect in the **network behavior** (drops, PDR), not in a flag the metrics
  can read directly. Otherwise detection becomes trivial and the result is worthless.

## Environment (verified on this machine)

- Windows, **no WSL distribution installed**, **no `gcc`**, **no `cmake`**.
- `python` → **3.11.8**; `pip` → 26.1.2; `git` → 2.50.1.windows.1.
- Installed and importable: `numpy 1.26.4`, `pandas 3.0.2`, `scikit-learn 1.8.0`,
  `scipy 1.17.1`, `matplotlib 3.10.8`, `seaborn 0.13.2`, `networkx 3.6.1`, `jupyterlab 4.5.6`,
  `simpy 4.1.2`.
- No MANET/AODV package exists on PyPI — see the simulator note above.

Version gotchas that will bite against older tutorials/code:

- **pandas 3.x**, not 2.x: Copy-on-Write is always on (the option is deprecated and inert),
  `DataFrame.applymap` is **removed** (use `DataFrame.map`), and string columns default to
  the `str` dtype.
- **numpy is 1.26.x**, not 2.x — numpy 2 migration notes do not apply here.
- scikit-learn 1.8 is newer than most tutorial pins; check `sklearn` API notes before
  copying snippets that assume ~1.0–1.2.

Use `python -m pip ...` rather than bare `pip` so the interpreter and the install match.

## Target repo layout

Matches the guide's prescribed structure:

```text
simulator/            # in-repo Python MANET simulator (replaces ns3/)
attacks/              # blackhole / grayhole behaviour strategies (injected into the simulator)
scenarios/            # one JSON config per experiment/scenario
traces/               # generated CSV traces          (gitignored)
data/                 # built datasets                (gitignored, keep samples)
feature_extraction/   # traces -> feature CSV
ml/                   # training/eval/pipeline code + saved model
results/              # metrics, plots, per-run records (gitignored except plots)
dashboard/            # optional viewer
docs/                 # notes, deviations, experiment log
```

- Git is initialised on `main` with no remote. `.gitignore` already covers `traces/`, `data/`
  and bulk `results/` output — keep it that way rather than committing generated data.
  The guide is explicit: **do not commit large generated trace files.** Commit code,
  scenario configs, small sample data, plots, and docs; archive big experiment outputs
  separately. Every result must be traceable back to a saved run.

## Non-negotiables (from the guide — these are the rules agents break by default)

**Gates — do not skip ahead:**

1. No ML work until the normal AODV simulation runs repeatably with sensible output.
2. No detector until the attack demonstrably changes measurable network behavior.
3. Data generation → baseline model → comparison → generalization, in that order.

**Evaluation integrity:**

4. **Never split by random rows.** Rows from one simulation run are correlated; a random row
   split inflates scores. Hold out by **scenario / seed / configuration**.
5. **No leakage features.** Do not add a feature that directly reveals attacker identity or
   the attack label (e.g. a `is_attacker` column, or any field derived from the attack config
   rather than from observed traffic).
6. **Never report accuracy alone.** Always report precision, recall, F1, false-positive rate,
   and a confusion matrix. Imbalanced security data can look perfect while missing most attacks.
7. **Always compare against plain AODV without IDS.** Report PDR, throughput, end-to-end delay,
   packet loss, routing overhead for both.
8. Every number in the report/README must trace to a saved experiment run + its config.

**Scope discipline (the guide's "Do Not Overbuild"):**

9. Do not start with six attacks, deep learning, federated learning, blockchain, or a mobile app.
   Attack order is **Blackhole first** (easy, direct PDR impact), then Grayhole, then flooding/DoS
   only if the first two are stable.
10. **Mentor checkpoint rule:** at the end of each week freeze a working version. If an advanced
    feature threatens the core demonstration, cut the advanced feature and keep the baseline.
11. Do not claim the model "detects all MANET attacks." State exactly which attacks, traffic
    conditions, mobility models, and simulator settings were evaluated.

**Acceptance criterion (the guide's definition of success)** — the deliverable is this chain,
reproducible on demand:
`launch simulation → generate normal/attack traffic → extract features → run trained IDS →
identify malicious node → trigger response → show measurable improvement vs. baseline AODV`.
A dashboard is secondary to this chain. Do not build one before the chain works.

## Known failure points (check these before debugging anything else)

- Model looks great on test data → suspect random row split (rule 4) or leakage (rule 5).
- Accuracy high but recall terrible → class imbalance; report the full metric set (rule 6).
- Attack has no measurable effect → the attack implementation is wrong; validate the attack
  *before* training anything (gate 2).
- Results change between identical runs → missing explicit seed / non-deterministic iteration
  order over sets.
- "ML improves the network" but no baseline table → rule 7 violated; the claim is unverifiable.
