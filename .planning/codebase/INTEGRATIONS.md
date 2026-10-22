# External Integrations

**Analysis Date:** 2026-10-22

> **Status legend.**
> - **[IMPLEMENTED]** — exists in the repo today.
> - **[SPECIFIED]** — mandated or directed by `AGENTS.md` / `MANET_IDS_BTech_Execution_Guide.md`, with the intended repo-relative path. **Not yet built.**
>
> **Verified repo contents (2026-10-22):** `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, and a git repo on branch `main` with one commit (`2246d39`) and **no remote configured**. No source code, no manifest, no CI, no test suite.

## Executive summary — read this first

**This project integrates with no external services. None. There are zero third-party APIs, zero databases, zero cloud providers, zero auth providers, zero webhooks, and zero CI pipelines — and none are planned.**

The "integrations" that exist are **all local and in-process**: the in-repo chain `simulator → attacks → traces → features → dataset → ML → IDS response → network re-evaluation` (`AGENTS.md:34-35`, `MANET_IDS_BTech_Execution_Guide.md:36-40`), and the **local filesystem** as the only persistence layer.

The two boundary rules that make this work, and which a future implementer must not break:

1. **`simulator/` must not import `attacks/`** (`AGENTS.md:67-69`). Attack behaviour is injected at run time by the scenario runner. This keeps the simulator attack-agnostic, so the *same* simulator code produces the clean baseline runs used for the IDS-off comparison (`AGENTS.md:150`). There is no plugin API, no entry-point registry, and no dynamic loading — just an injected object.
2. **Labels come from the scenario config, never from the trace** (`AGENTS.md:84-85`). The ground truth is an input, not a derived quantity. Any integration that let the trace reveal the attacker would break evaluation integrity (rule 5, `AGENTS.md:145-146`).

## APIs & External Services

**None.**

- No REST/GraphQL API is consumed. No API keys, no tokens, no OAuth.
- No third-party SaaS (no Stripe, no Supabase, no Sentry, no Datadog, no OpenAI/Anthropic API, no MLflow, no W&B, no Airflow, no cloud queue).
- `requests 2.32.5` and `pydantic 2.12.5` happen to be present in the environment, but **nothing in the spec calls for HTTP**. Adding a network call to the simulator or ML pipeline would break the "runs natively on Windows, entirely locally" property (`AGENTS.md:27`) and the reproducibility guarantee.
- **The only "API" in this system is the internal module contract** documented below.

### Internal module contracts (the real integration surface)

| # | Boundary | From → To | Contract | Status |
|---|----------|-----------|----------|--------|
| 1 | Scenario config → simulator | `scenarios/*.json` → `simulator/run_scenario.py` | JSON: node count, area, mobility model/speed, traffic flows, seed, attack type, attacker node id | **[SPECIFIED]** |
| 2 | Attack injection | `attacks/` → `simulator/aodv.py` | Node **behaviour flags** on the AODV node: a lying RREP (blackhole) and probabilistic drop (grayhole). Injected by the runner, never imported by `simulator/`. | **[SPECIFIED]** `AGENTS.md:61-69` |
| 3 | Simulator → trace | `simulator/` → `traces/*.csv` | CSV, one row per packet event: `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` | **[SPECIFIED]** `AGENTS.md:81-83` |
| 4 | Trace → features | `traces/*.csv` → `feature_extraction/` → `data/*.csv` | Per-node, per-fixed-time-window feature rows (schema in § Data Storage). Features are **derived from** traces, never embedded in them. | **[SPECIFIED]** `AGENTS.md:83`, guide §3 Module C |
| 5 | Dataset → ML | `data/*.csv` → `ml/` | Label column + 10 features; split by **scenario/seed group**, not by row | **[SPECIFIED]** `AGENTS.md:142-143` |
| 6 | ML → model artifact | `ml/` → saved model + preprocessing pipeline | `sklearn.pipeline.Pipeline` (scaler + classifier) persisted via `joblib`; both must be saved | **[SPECIFIED]** guide §3 Module D, `MANET_IDS_BTech_Execution_Guide.md:127,329` |
| 7 | ML → response | `ml/` → `simulator/` | IDS prediction → alert above a confidence threshold → node marked malicious / low-trust → route selection avoids it | **[SPECIFIED]** guide §3 Module E, `AGENTS.md:128-133` |
| 8 | Response → re-evaluation | `simulator/` → `results/` | Re-run the **same scenario and seed** with IDS on vs. off; report PDR, throughput, end-to-end delay, packet loss, routing overhead for both | **[SPECIFIED]** `AGENTS.md:150`, `MANET_IDS_BTech_Execution_Guide.md:255-259` |

> **Boundary 7 is the one that is easiest to get wrong.** The IDS response must act on the *simulator's* routing decisions, not on a post-hoc analysis script. `MANET_IDS_BTech_Execution_Guide.md:133` — "Re-run the same scenario and quantify whether network performance improves." The comparison is only meaningful if the "IDS on" run uses the identical scenario config and seed as the "IDS off" run.

## Data Storage

**Databases:**
- **None.** No PostgreSQL, MySQL, SQLite, MongoDB, Redis, Neo4j, or any DB engine. No ORM (no SQLAlchemy, no Django ORM, no Prisma).
- **Rationale:** the entire dataset is a set of CSV files on the local disk. Adding a database would add a dependency, a service to install, and a portability constraint — for zero benefit at this scale (`MANET_IDS_BTech_Execution_Guide.md:322-328` lists "clean datasets or dataset-generation scripts" as the deliverable, not a database).
- **Do not add one.** If a future phase wants queryable data, the answer is a `pandas`/CSV pipeline or a small SQLite file, not a server.

**File Storage:**
- **Local filesystem only.** No S3, no GCS, no Azure Blob, no Cloudflare R2, no Dropbox/Drive sync, no OCI registry, no container volume.

| Path | Format | Contents | Git policy |
|------|--------|----------|------------|
| `scenarios/*.json` | JSON | One config per experiment: topology, mobility, traffic, seed, attack + attacker id | **Commit** (`AGENTS.md:129`) |
| `traces/*.csv` | CSV | Raw packet-event traces, one row per event: `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` | **Ignored** — `.gitignore:2` |
| `data/*.csv` | CSV | Feature table, one row per node per observation window | **Ignored** — `.gitignore:3` (small samples may be committed; `AGENTS.md:118` says "gitignored, keep samples") |
| `ml/` | `.joblib` / `.pkl` | Saved model **and** preprocessing pipeline | Commit the code; the model artifact is a deliverable (`MANET_IDS_BTech_Execution_Guide.md:329`) — decide and record whether the binary is committed or archived |
| `results/` | JSON/CSV + figures | Per-run records, metrics, confusion matrices, plots | Bulk ignored, `results/plots/` **committed** — `.gitignore:6-7` |
| `docs/` | Markdown | Notes, deviations, experiment log | **Commit** |
| `dashboard/` | Python/HTML | Optional viewer | **Commit** (source) |
| `requirements.txt` | Text | Pinned dependency manifest — **does not exist yet** | **Commit** (once created) |

- **Trace format is fixed by spec** (`AGENTS.md:81-83`): one row per packet event, columns beginning `time, src, dst, pkt_id, type, hop_count, dropped_by, ...`. Keep this column set stable — `feature_extraction/` and any downstream notebook depend on it.
- **Feature schema is fixed by spec** (`MANET_IDS_BTech_Execution_Guide.md:104-117`), one row per observation window or node:
  `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`, `label`.
  - `label` ∈ {Normal, Blackhole, Grayhole, other} — sourced from the scenario config, **never** computed from the trace.
  - **No leakage columns.** No `is_attacker`, no `attack_type_in_trace`, no field derived from the attack config rather than observed traffic (`AGENTS.md:145-146`, `MANET_IDS_BTech_Execution_Guide.md:315`).
- **Windows path safety:** the repo root contains spaces. Use `pathlib.Path` everywhere; never build paths with `+` or hard-coded separators.

**Caching:**
- **None.** No Redis, no memcached, no in-process cache layer, no `functools.lru_cache` across runs.
- The only caching-like behaviour is legitimate and local: re-running the *same* scenario+seed must reproduce byte-identical traces (`AGENTS.md:72-74`). That is determinism, not caching — never "cache" a run to make results look stable.

## Authentication & Identity

**None.**
- No auth provider (no Auth0, Firebase, Clerk, Keycloak, NextAuth, OAuth, SAML, LDAP).
- No session, no JWT, no cookie, no API key, no `.env` holding credentials, no secrets manager. There are no secrets in this project because there is nothing to authenticate against.
- **Node identity is a simulation-internal integer**, not a user identity: `src`/`dst` in the trace, `attacker node id` in the scenario config, and the `label` in the feature table. These are labels, not principals.
- **Do not add login/auth to the optional dashboard.** If a dashboard is ever built, it binds to `127.0.0.1` only. `MANET_IDS_BTech_Execution_Guide.md:147` treats the dashboard as optional and `AGENTS.md:166-167` subordinates it to the acceptance chain.

## Monitoring & Observability

**Error Tracking:**
- **None.** No Sentry, no Rollbar, no Bugsnag, no Honeybadger, no `raygun`.

**Logs:**
- **No logging framework is configured.** The stdlib `logging` module is available and is the correct choice — no `loguru`, no `structlog`.
- **The project's real observability is the metrics artifact**, not log scraping: PDR, throughput, end-to-end delay, packet loss, routing overhead (`AGENTS.md:150`, `MANET_IDS_BTech_Execution_Guide.md:255-259`), plus IDS processing time and added routing/communication overhead (`MANET_IDS_BTech_Execution_Guide.md:259`).
- **Prescriptive:** write a per-run record under `results/` capturing the scenario config path, the seed, the metric set, and the timestamp, so every number in the report can be traced to a saved run (`AGENTS.md:151`, `MANET_IDS_BTech_Execution_Guide.md:320`). Console output is for the operator; `results/` is for the record.
- **No metrics scraping, no Prometheus, no OpenTelemetry, no Grafana, no uptime checks.** There is no long-running service to monitor.

**Plots (the visible observability surface):**
- `results/plots/` — confusion matrix per classifier, precision/recall/F1 comparison bar chart, PDR vs. number of malicious nodes, throughput vs. attack intensity, end-to-end delay with IDS OFF vs. ON, detection rate vs. mobility speed (`MANET_IDS_BTech_Execution_Guide.md:263-270`).
- Built with matplotlib 3.10.8 + seaborn 0.13.2. Set `matplotlib.use("Agg")` in any script that renders headlessly.

## CI/CD & Deployment

**Hosting:**
- **None.** No cloud provider, no VPS, no container registry, no PaaS, no static host, no serverless. Everything runs on the developer's Windows machine.
- The only "hosting" that exists is the local filesystem described in § Data Storage.

**CI Pipeline:**
- **None.** No `.github/workflows/`, no `.gitlab-ci.yml`, no `azure-pipelines.yml`, no Jenkinsfile, no `tox.ini`, no pre-commit hook (`.gitignore` does not exclude `.git/hooks/`, and `git log` shows a single manual commit).
- **The git repository has no remote** (`AGENTS.md:6-7`; `git remote -v` returns empty). There is nothing to push to and no CI to trigger. GitHub is listed only as the eventual version-control target in `MANET_IDS_BTech_Execution_Guide.md:145,153` ("Install Git and create a private/public repository").
- **Do not add CI or a remote without an explicit decision.** The guide's Day-1 deliverable is "Create Git repository" (`MANET_IDS_BTech_Execution_Guide.md:278`) — which is done locally. The engineering contract says "everything stays local until a remote is deliberately added" (`AGENTS.md:7`).
- **Do not add a `requirements.txt` install + pytest step to any hosted CI** until a remote exists; a lockstep manifest is a local artifact.

**Deployment target:**
- **Not applicable.** The project's "release" is a **reproducible on-demand run** of the acceptance chain: `launch simulation → generate normal/attack traffic → extract features → run trained IDS → identify malicious node → trigger response → show measurable improvement vs. baseline AODV` (`AGENTS.md:163-166`, `MANET_IDS_BTech_Execution_Guide.md:379`).
- Committing to git, and archiving large experiment outputs separately (`AGENTS.md:130`), are the only "publish" steps.

## Environment Configuration

**Required env vars:**
- **None.** The specified pipeline is fully driven by `scenarios/*.json` plus the `--seed` CLI argument to `simulator/run_scenario.py` (`AGENTS.md:65`). There are no API keys, no database URLs, no cloud credentials.
- **No `.env` file exists, and none is required.** `.gitignore` does not list `.env`, which is consistent with there being no secrets to hide — but if one is ever introduced, add it to `.gitignore` in the same commit and keep it to non-secret local settings only.
- **Optional (only if the optional dashboard is built):** a bind host/port (e.g. `DASHBOARD_HOST=127.0.0.1`, `DASHBOARD_PORT=8000`) and a results directory path. These are conveniences, not secrets.

**Secrets location:**
- **None. There are no secrets in this project.** Do not introduce any.

**The actual configuration surface a future implementer MUST respect:**
- `scenarios/*.json` — the authoritative configuration and label source. `AGENTS.md:84-85`.
- `--seed <int>` — the determinism switch. Same seed ⇒ identical traces. `AGENTS.md:72-74`.
- `--out <dir>` — where traces and run records land. `AGENTS.md:65`.

## Webhooks & Callbacks

**Incoming:**
- **None.** No HTTP server, no route handlers, no GraphQL subscriptions, no queue consumers, no event bus, no message broker (no Kafka, no RabbitMQ, no SQS, no Redis Streams).
- `simulator/run_scenario.py` is a **CLI**, not a server. Do not add a `Flask`/`FastAPI`/`aiohttp` server to `simulator/` — the simulator is invoked as a subprocess or imported, and adding a server would put the experiment matrix behind a runtime that has no reason to exist.

**Outgoing:**
- **None.** No outbound HTTP, no SMTP, no Slack/Teams/Telegram/Discord bot, no SMS, no push notification, no telemetry beacon, no analytics.

**Callback surface that *does* exist (internal, in-process):**
- The IDS **response hook** is a callback, but it is an ordinary Python function call inside the simulation loop, not a network callback. `AGENTS.md:128-133`, guide §3 Module E.
- The **retry/timeout** mechanisms are SimPy `env.timeout()` events inside `simulator/aodv.py`, not HTTP retries.

## What MUST NOT be added

These are the integration-shaped additions that would violate the project's stated constraints. Treat each as a review rejection:

| Do not add | Why | Source |
|---|---|---|
| NS-3 / `ns-3-dev` / any C++ toolchain | Dropped; installation "will fail and it is out of scope" | `AGENTS.md:26,30-31` |
| Any network API call from `simulator/`, `feature_extraction/`, or `ml/` | Breaks the local-only, reproducible property; no service to call | `AGENTS.md:27` |
| A database | CSVs are the specified storage; a DB adds a service and a dependency for no gain | `MANET_IDS_BTech_Execution_Guide.md:322-328` |
| Auth in the optional dashboard | No users exist; dashboard binds to `127.0.0.1` | `MANET_IDS_BTech_Execution_Guide.md:147` |
| CI/CD or a git remote | "everything stays local until a remote is deliberately added" | `AGENTS.md:6-7` |
| `simulator/` importing `attacks/` | Breaks attack-agnosticism and therefore the baseline comparison | `AGENTS.md:67-69` |
| A dashboard before the acceptance chain works | "A dashboard is secondary to this chain." | `AGENTS.md:166-167` |
| Blockchain / federated learning / deep learning / mobile app | Scope discipline; do not start with six attacks and four extra subsystems | `AGENTS.md:155`, `MANET_IDS_BTech_Execution_Guide.md:59` |
| SHAP / XGBoost / online learning as a *starting* point | Stretch features only, after the core works | `MANET_IDS_BTech_Execution_Guide.md:68-75` |
| A cloud backup/archival service for large traces | "archive big experiment outputs separately" — separately, not necessarily to a cloud | `AGENTS.md:129-130` |

## The only external touchpoints, summarised

| Touchpoint | Type | State |
|---|---|---|
| Git repository (branch `main`, no remote) | VCS | **[IMPLEMENTED]** — local only |
| Local filesystem (`traces/`, `data/`, `results/`, `ml/`, `docs/`, `scenarios/`) | Storage | **[IMPLEMENTED]** (directories not yet created) |
| `scenarios/*.json` → runner | Config contract | **[SPECIFIED]** `AGENTS.md:116` |
| `attacks/` → `simulator/` (injected) | In-process contract | **[SPECIFIED]** `AGENTS.md:61-69` |
| `traces/` → `feature_extraction/` → `data/` | File contract | **[SPECIFIED]** `AGENTS.md:81-83` |
| `data/` → `ml/` → saved model | File + object contract | **[SPECIFIED]** guide §3 Module D |
| `ml/` → IDS response → `simulator/` | In-process callback | **[SPECIFIED]** guide §3 Module E |
| Optional local dashboard (FastAPI/Flask; both present in env, none specified) | Local HTTP, `127.0.0.1` | **[SPECIFIED — optional, last]** `MANET_IDS_BTech_Execution_Guide.md:147,332` |
| GitHub (future VCS target) | Hosted git | **Not detected** — no remote configured; no action required |

---

*Integration audit: 2026-10-22 — derived from `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, and direct inspection of the repository and the installed Python 3.11.8 environment. No packages were installed and no network or package-manager write commands were run.*
