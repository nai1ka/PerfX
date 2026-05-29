# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

PerfX is a performance monitoring and regression detection system for Android apps. An embeddable Android SDK collects on-device metrics, a Ktor backend ingests them, ClickHouse stores the time series, a Python service detects regressions, and a Streamlit dashboard surfaces results.

## Repository layout

Four largely independent sub-projects, each with its own build/run lifecycle:

- `Android/PerfX/` — Gradle multi-module project: `:sdk` (the embeddable library) and `:demo` (reference integration).
- `Backend/` — Ktor REST API (`Backend/app`), plus `docker-compose.yml` orchestrating Postgres + ClickHouse + the backend.
- `Analysis/` — Python regression detection service and exploratory notebooks.
- `Frontend/` — Streamlit web dashboard.
- `Demo/` — third-party Android apps (2048, Paint) used as integration test targets; not part of the PerfX build.
- `Thesis/` — LaTeX source for the Bachelor's thesis documenting this project. Ships its own `Thesis/CLAUDE.md` with extensive thesis-editing rules; consult it (it is auto-loaded) before doing any work on the thesis text.

## Commands

### Backend
```bash
cd Backend && docker compose up --build          # Postgres :5432, ClickHouse :8123/:9000, Ktor :8080
cd Backend/app && ./gradlew run                  # run backend alone (needs Postgres + ClickHouse reachable)
cd Backend/app && ./gradlew test                 # run tests
cd Backend/app && ./gradlew test --tests "ClassName.methodName"   # single test
```

### Android SDK / demo
```bash
cd Android/PerfX && ./gradlew :sdk:assembleDebug
cd Android/PerfX && ./gradlew :demo:installDebug
cd Android/PerfX && ./gradlew :sdk:testDebugUnitTest                              # all SDK unit tests
cd Android/PerfX && ./gradlew :sdk:testDebugUnitTest --tests "com.ndevelop.sdk.ExampleUnitTest"
cd Android/PerfX && ./gradlew :sdk:lint                                          # Android lint
cd Android/PerfX && ./gradlew :sdk:publishToMavenLocal                           # publish com.ndevelop:perfx-sdk:1.0.0
```

### Regression detector
```bash
cd Analysis && pip install -r requirements.txt && python regression_detector.py   # runs forever, polls every 60s
```

### Frontend
```bash
cd Frontend && pip install -r requirements.txt && streamlit run app.py            # dashboard at :8501
```

### Thesis (LaTeX)
```bash
cd Thesis && latexmk -pdf thesis.tex     # builds thesis.pdf; biblatex with the biber backend
```
`thesis.tex` `\include`s the chapter files from `Thesis/chapters/`. The byte-identical copies at the `Thesis/` root (`Thesis/chapter1.tex`, etc.) are stale and unused — always edit the `Thesis/chapters/` versions. See `Thesis/CLAUDE.md` for editing conventions and note its rule against compiling unless explicitly asked.

## Architecture

### Data flow
1. The SDK's `PerfX` object (`Android/PerfX/sdk/.../PerfX.kt`) registers `PerformanceCollector`s (CPU, frame time, RAM, one-shot startup time). Metrics are buffered in a local Room DB and batch-uploaded to the backend `POST /ingest` (default endpoint `http://10.0.2.2:8080/` — the emulator alias for host localhost). The in-repo `:demo` module depends on `:sdk` directly via `project(":sdk")`; external host apps (e.g. the `Demo/` apps) consume the published `com.ndevelop:perfx-sdk` artifact from Maven Local instead.
2. The Ktor backend (`Backend/app`) writes raw metrics into ClickHouse table `metrics.metric_records` and serves authenticated query endpoints. Users, projects, thresholds and confirmed regressions live in Postgres.
3. The regression detector (`Analysis/`) reads recent windows from ClickHouse, runs a Rolling Window Percentile Shift comparison plus a Mann-Whitney U test, and inserts confirmed regressions into Postgres.
4. The Streamlit dashboard calls the backend REST API to render metrics, custom plots, and regression reports.

### Two-database split
- **ClickHouse** (`metrics` db) — time-series metric data only. Schema in `Backend/clickhouse/init/01_schema.sql`; `metric_records` is a MergeTree partitioned by day, ordered by `(project_id, metric_id, ts)`.
- **Postgres** (`perfx` db) — relational state: users, projects, per-project regression thresholds, confirmed regressions. Schema in `Backend/postgres/init/`.

### Backend (Ktor)
- Entry point `Application.kt` installs serialization, security (JWT), databases, then `configureRouting`.
- `Routing.kt` holds all endpoints. Auth (`/auth/login`, `/auth/signup`) uses BCrypt + JWT. Project/metric/regression endpoints sit behind the `auth-jwt` block and check `isProjectOwnedByUser` for tenancy isolation.
- `/ingest` is intentionally unauthenticated (the SDK posts to it).
- ClickHouse access goes through `ClickHouseClient` over its HTTP interface; SQL strings are built inline in `Routing.kt`.

### Regression detection
- `Analysis/regression_detection/config.py` holds detection parameters: baseline vs. current window sizes, default P95 degradation threshold (`DEFAULT_P95_THRESHOLD`), p-value, and `MIN_SAMPLES`. The window values in `config.py` are currently set to small numbers for local testing — comments describe the intended production values.
- Thresholds resolve in a fallback chain: exact `(project, metric, screen)` → project-wide `(project, metric, None)` → `DEFAULT_P95_THRESHOLD`.

## Evaluation / validation setup

Overhead experiments were run on three AVDs and one physical device:

| Name | Type | Android API | RAM | CPU cores | Cohort |
|---|---|---|---|---|---|
| `PerfX_Low` | AVD (arm64-v8a) | 30 (Android 11) | 2 GB | 2 | Low |
| `PerfX_Medium` | AVD (arm64-v8a) | 33 (Android 13) | 4 GB | 4 | Medium |
| `PerfX_High` | AVD (arm64-v8a) | 34 (Android 14) | 8 GB | 4 | High |
| `Redmi_Note_9_Pro` | Physical device | — | — | — | Real device |

Results for each target live in `Android/evaluation/results/<name>/` (four files per run: `noSdk.csv`, `withSdk.csv`, `noSdk_startup.txt`, `withSdk_startup.txt`).

### Evaluation scripts

| Script | Purpose |
|---|---|
| `Android/evaluation/utils/generate_emulators.sh` | Create and configure the three AVDs from scratch |
| `Android/evaluation/run/run_overhead_on_avd.sh <avd-name>` | Launch a named AVD, run both flavors, copy results |
| `Android/evaluation/measure/measure_overhead.sh <flavor>` | Measure CPU/RAM/startup for one flavor on the running device |
| `Android/evaluation/measure/measure_accuracy.sh` | Accuracy experiment (ground-truth metric comparison) |
| `Android/evaluation/run/run_regression_experiments.py` | Regression-detection experiment driver |
| `Android/evaluation/analysis/` | Python notebooks/scripts that post-process CSVs into charts |

The `noSdk`/`withSdk` flavors are variants of the `:demo` app built with and without the SDK injected, controlled by a Gradle product flavor.

## Conventions

- SDK and demo code use package `com.ndevelop.*`; backend uses `com.perfx.*`.
- JVM toolchains differ: the backend targets JDK 21 (`Backend/app/build.gradle.kts`, also pinned in `Backend/app/Dockerfile`), while the Android SDK targets JDK 17. The README's "JDK 17+" understates the backend requirement.
- DB credentials are hardcoded in `docker-compose.yml`, `Analysis/regression_detection/config.py`, and read from env vars in the backend — keep these three in sync when changing them.
- `Frontend/.history/` and `.history/` (repo root) contain editor history snapshots; ignore them.
