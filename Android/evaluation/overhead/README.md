# Overhead experiments (Chapter 4)

---

### `run_overhead_on_avd.sh`
Launches a named AVD, runs both `noSdk` and `withSdk` flavors back-to-back,
and copies results to `../results/<avd-name>/`.

```bash
./run_overhead_on_avd.sh PerfX_Medium
```

### `measure_overhead.sh`
Measures CPU/RAM/startup for one app flavor on the currently connected device.
Called automatically by `run_overhead_on_avd.sh`; can also be run standalone.

```bash
./measure_overhead.sh withSdk [--build]
./measure_overhead.sh noSdk
```

### `measure_accuracy.sh`
Collects ground-truth metrics via `adb` for the SDK accuracy experiment.

```bash
./measure_accuracy.sh [--build]
```

### `generate_emulators.sh`
One-time setup: creates the three AVDs (`PerfX_Low`, `PerfX_Medium`,
`PerfX_High`) from scratch.

```bash
./generate_emulators.sh
```
