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

### Docker images (publish to Docker Hub)

Images are built with **Docker Buildx** (builder name `perfx-builder`, registry `nai1ka/`). Always use `buildx build --push`, never plain `docker build`.

```bash
# Ensure the builder is active (created once, reused after)
docker buildx inspect perfx-builder &>/dev/null || docker buildx create --name perfx-builder --use
docker buildx use perfx-builder

# Build and push a single image
docker buildx build --platform linux/amd64 --push -t nai1ka/perfx-frontend  Frontend/
docker buildx build --platform linux/amd64 --push -t nai1ka/perfx-detector  Analysis/
docker buildx build --platform linux/amd64 --push -t nai1ka/perfx-backend   Backend/app
docker buildx build --platform linux/amd64 --push -t nai1ka/perfx-postgres  Backend/postgres
docker buildx build --platform linux/amd64 --push -t nai1ka/perfx-clickhouse Backend/clickhouse

# Or use the helper script to build all at once
bash scripts/build-and-push.sh nai1ka
```

Image → source directory mapping:
| Image | Source |
|---|---|
| `nai1ka/perfx-backend` | `Backend/app` |
| `nai1ka/perfx-frontend` | `Frontend/` |
| `nai1ka/perfx-detector` | `Analysis/` |
| `nai1ka/perfx-postgres` | `Backend/postgres` |
| `nai1ka/perfx-clickhouse` | `Backend/clickhouse` |

### Thesis (LaTeX)
```bash
cd Thesis && latexmk -pdf thesis.tex     # builds thesis.pdf; biblatex with the biber backend
```
`thesis.tex` `\include`s the chapter files from `Thesis/chapters/`. The byte-identical copies at the `Thesis/` root (`Thesis/chapter1.tex`, etc.) are stale and unused — always edit the `Thesis/chapters/` versions. See `Thesis/CLAUDE.md` for editing conventions and note its rule against compiling unless explicitly asked.

## Architecture

### Data flow
1. The SDK's `PerfX` object (`Android/PerfX/sdk/.../PerfX.kt`) registers `PerformanceCollector`s (CPU, frame time, RAM, one-shot startup time). Metrics are buffered in a local Room DB and batch-uploaded to the backend `POST /ingest` (default endpoint `https://api.perfx.ru/` — the emulator alias for host localhost). The in-repo `:demo` module depends on `:sdk` directly via `project(":sdk")`; external host apps (e.g. the `Demo/` apps) consume the published `com.ndevelop:perfx-sdk` artifact from Maven Local instead.
2. The Ktor backend (`Backend/app`) writes raw metrics into ClickHouse table `metrics.metric_records` and serves authenticated query endpoints. Users, projects, version releases, and confirmed regressions live in Postgres (there is no `thresholds` table).
3. The regression detector (`Analysis/`) groups samples by version code and compares each consecutive release pair by the relative P95 shift per (metric, screen, cohort) group — no time windows and no hypothesis test. It inserts confirmed regressions into Postgres, and pushes a Telegram alert via `notifier.py` when the project is linked to a chat (`telegram_bot.py`).
4. The Streamlit dashboard calls the backend REST API to render metrics, custom plots, and regression reports.

### Two-database split
- **ClickHouse** (`metrics` db) — time-series metric data only. Schema in `Backend/clickhouse/init/01_schema.sql`; `metric_records` is a MergeTree partitioned by day, ordered by `(project_id, metric_id, ts)`.
- **Postgres** (`perfx` db) — relational state: users, projects, `version_releases` (version catalogue synced from ClickHouse by `VersionSyncJob` every ~5 min), confirmed regressions. No `thresholds` table. Schema in `Backend/postgres/init/`.

### Backend (Ktor)
- Entry point `Application.kt` installs serialization, security (JWT), databases, then `configureRouting`.
- `Routing.kt` holds all endpoints. Auth (`/auth/login`, `/auth/signup`) uses BCrypt + JWT. Project/metric/regression endpoints sit behind the `auth-jwt` block and check `isProjectOwnedByUser` for tenancy isolation.
- `/ingest` is intentionally unauthenticated (the SDK posts to it).
- ClickHouse access goes through `ClickHouseClient` over its HTTP interface; SQL strings are built inline in `Routing.kt`.

### Regression detection
- `Analysis/regression_detection/config.py` holds detection parameters: a single global `DEFAULT_P95_THRESHOLD` (0.15) applied to every group, and `MIN_SAMPLES_PER_VERSION`. There is **no** per-project/per-metric threshold table and **no** fallback chain — the old `thresholds` table was removed. Values are small for local testing; comments note the intended production values.
- A regression is flagged when the relative P95 shift between two consecutive version codes exceeds the threshold. Regression `status` is `open`/`closed` only and is closed **manually** from the dashboard — there is no automatic close (the superseded/rolled-back logic was removed).
- CPU usage (`Android/PerfX/sdk/.../trackers/CpuCollector.kt`) is `process CPU time / wall-clock time × 100`; it can exceed 100% on multi-core devices and is **not** normalised by system CPU or by core count.

## Evaluation / validation setup

Overhead experiments were run on three AVDs and one physical device:

| Name | Type | Android API | RAM | CPU cores | Cohort |
|---|---|---|---|---|---|
| `PerfX_Low` | AVD (arm64-v8a) | 30 (Android 11) | 2 GB | 2 | Low |
| `PerfX_Medium` | AVD (arm64-v8a) | 33 (Android 13) | 4 GB | 4 | Medium |
| `PerfX_High` | AVD (arm64-v8a) | 34 (Android 14) | 8 GB | 4 | High |
| `Redmi_Note_9_Pro` | Physical device | — | — | — | Real device |

Results for each target live in `Android/evaluation/results/<name>/` (four files per run: `noSdk.csv`, `withSdk.csv`, `noSdk_startup.txt`, `withSdk_startup.txt`).

### Overhead evaluation scripts

| Script | Purpose |
|---|---|
| `Android/evaluation/utils/generate_emulators.sh` | Create and configure the three AVDs from scratch |
| `Android/evaluation/run/run_overhead_on_avd.sh <avd-name>` | Launch a named AVD, run both flavors, copy results |
| `Android/evaluation/measure/measure_overhead.sh <flavor>` | Measure CPU/RAM/startup for one flavor on the running device |
| `Android/evaluation/measure/measure_accuracy.sh` | Accuracy experiment (ground-truth metric comparison) |

The `noSdk`/`withSdk` flavors are variants of the `:demo` app built with and without the SDK injected, controlled by a Gradle product flavor.

### Regression-detection validation (Chapter 5 thesis evaluation)

Build-time regression injection lets each APK bake in a synthetic regression via Gradle properties:

```bash
cd Android/PerfX
./gradlew :demo:assembleWithSdkDebug \
  -PsyntheticVersionCode=1001 -PsyntheticVersionName=1.0.1-clean \
  -PregressionType=none -PregressionIntensity=0 -PtargetScreen=cpu_load

./gradlew :demo:assembleWithSdkDebug \
  -PsyntheticVersionCode=1002 -PsyntheticVersionName=1.0.2-cpu-med \
  -PregressionType=cpu -PregressionIntensity=2 -PtargetScreen=cpu_load
```

Regression types: `cpu` | `memory` | `ui` | `startup` | `interaction` | `none`
Intensity: `1` (low) · `2` (medium) · `3` (high)

The baked regression activates in `DemoApp.onCreate()` via `RegressionInjector`.
The `navigate_to` intent extra controls which screen the app opens on launch.

#### Experiment driver

```bash
cd Android/evaluation/run

# Full matrix on one device (~12 h at 15 min/version)
python3 run_release_pair_experiments.py \
  --project-id c0fabf43-bbd4-4f9e-bdab-ee5019727b00 --device PerfX_Medium

# Quick smoke test — one experiment (~8 min at 2 min/version)
python3 run_release_pair_experiments.py \
  --project-id c0fabf43-bbd4-4f9e-bdab-ee5019727b00 \
  --device PerfX_Medium --experiments e1_cpu_high
```

Experiment matrix: `Android/evaluation/run/experiments.yaml`
Results: `Android/evaluation/results/release_pair/<timestamp>_<device>.csv`

The Docker Compose `detector` service handles detection automatically (polls every 30 s).

**Test-mode settings** (smoke tests):
- `experiments.yaml`: `run_duration_minutes: 2`, `flush_wait_seconds: 15`
- `Analysis/regression_detection/config.py`: `MIN_SAMPLES_PER_VERSION: 10`

**Production settings** (thesis data):
- `experiments.yaml`: `run_duration_minutes: 15`, `flush_wait_seconds: 60`
- `config.py`: `MIN_SAMPLES_PER_VERSION: 50`

#### Analysis scripts

```bash
cd Android/evaluation/analysis
python3 aggregate_results.py     # → summary_e1/e2/e6.csv
python3 threshold_sweep.py       # → summary_e3.csv
python3 sample_size_sweep.py \   # → summary_e5.csv
  --project-id ... --baseline-vc 1003 --current-vc 1004 \
  --metric-id cpuUsage --screen-name "compose/cpu_load"
python3 plots.py                 # → analysis/figs/*.pdf
python3 tables.py                # prints LaTeX \begin{table} blocks
```

Use the `/run-validation` skill for step-by-step guidance on running the full pipeline.

## Conventions

- SDK and demo code use package `com.ndevelop.*`; backend uses `com.perfx.*`.
- JVM toolchains differ: the backend targets JDK 21 (`Backend/app/build.gradle.kts`, also pinned in `Backend/app/Dockerfile`), while the Android SDK targets JDK 17. The README's "JDK 17+" understates the backend requirement.
- DB credentials are hardcoded in `docker-compose.yml`, `Analysis/regression_detection/config.py`, and read from env vars in the backend — keep these three in sync when changing them.
- `Frontend/.history/` and `.history/` (repo root) contain editor history snapshots; ignore them.
