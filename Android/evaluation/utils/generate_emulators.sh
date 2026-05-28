#!/bin/bash

# Ensure SDK tools are on PATH (adjust if your Android Studio is elsewhere)
export ANDROID_HOME=~/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/emulator

# ── 1. Download ARM64 system images ──────────────────────────────────────────
sdkmanager "system-images;android-30;google_apis;arm64-v8a"
sdkmanager "system-images;android-33;google_apis;arm64-v8a"
sdkmanager "system-images;android-34;google_apis;arm64-v8a"

# ── 2. Create AVDs ───────────────────────────────────────────────────────────
echo "no" | avdmanager create avd -n "PerfX_Low"    -k "system-images;android-30;google_apis;arm64-v8a"
echo "no" | avdmanager create avd -n "PerfX_Medium" -k "system-images;android-33;google_apis;arm64-v8a"
echo "no" | avdmanager create avd -n "PerfX_High"   -k "system-images;android-34;google_apis;arm64-v8a"

# ── 3. Patch RAM and CPU cores in each config.ini ────────────────────────────
set_prop() {
  local file="$1" key="$2" val="$3"
  if grep -q "^${key}=" "$file"; then
    sed -i '' "s|^${key}=.*|${key}=${val}|" "$file"
  else
    echo "${key}=${val}" >> "$file"
  fi
}

AVD_DIR="$HOME/.android/avd"

# Low: 2 GB RAM, 2 cores  → cohort Low   (RAM ≤ 3 GB)
set_prop "$AVD_DIR/PerfX_Low.avd/config.ini"    hw.ramSize   2048
set_prop "$AVD_DIR/PerfX_Low.avd/config.ini"    hw.cpu.ncore 2

# Medium: 4 GB RAM, 4 cores → cohort Medium (RAM ≤ 6 GB, cores ≤ 8)
set_prop "$AVD_DIR/PerfX_Medium.avd/config.ini" hw.ramSize   4096
set_prop "$AVD_DIR/PerfX_Medium.avd/config.ini" hw.cpu.ncore 4

# High: 8 GB RAM, 4 cores  → cohort High   (RAM > 6 GB)
set_prop "$AVD_DIR/PerfX_High.avd/config.ini"   hw.ramSize   8192
set_prop "$AVD_DIR/PerfX_High.avd/config.ini"   hw.cpu.ncore 4

echo "Done. Verify with: avdmanager list avd"