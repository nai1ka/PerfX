import pandas as pd
import plotly.express as px
import streamlit as st

from menu import menu_with_redirect
from api_client import (
    get_regressions,
    get_releases,
    patch_regression,
    get_raw_values,
)
from session_restore import restore_session
from utils.ui import show_error, show_page_title

show_page_title("Regressions", "Version-based performance regressions")
restore_session()
menu_with_redirect()

project_id = st.session_state.get("project_id")

# ── Load data ─────────────────────────────────────────────────────────────────

try:
    releases_raw = get_releases(project_id=project_id)
    rows_raw     = get_regressions(project_id=project_id)
except Exception as e:
    show_error("Failed to load data", e)
    st.stop()

releases_df = pd.DataFrame(releases_raw) if releases_raw else pd.DataFrame()

if not rows_raw:
    st.info("No regressions recorded yet.")
    st.stop()

df = pd.DataFrame(rows_raw)
df["detected_at"] = pd.to_datetime(df["detected_at"], utc=True, errors="coerce")
for col in ("degradation_percent", "baseline_p50", "current_p50"):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Derived severity label
def _severity(pct):
    if pd.isna(pct):
        return "unknown"
    if pct >= 30:
        return "critical"
    if pct >= 10:
        return "high"
    return "low"

df["severity"] = df["degradation_percent"].apply(_severity)

# Normalise backend statuses to two UI statuses
df["status"] = df["status"].replace({"acknowledged": "closed", "resolved": "closed"})

# Human-readable version pair label
df["version_pair"] = df.apply(
    lambda r: f"v{r['baseline_version_name']} → v{r['current_version_name']}",
    axis=1,
)

# ── Filters ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Filters")

    status_opts = ["all", "open", "closed"]
    sel_status  = st.selectbox("Status", status_opts, index=0)

    severity_opts = ["all", "critical", "high", "low", "unknown"]
    sel_severity  = st.multiselect("Severity", severity_opts[1:], default=[])

    metric_opts = ["All"] + sorted(df["metric_id"].unique().tolist())
    sel_metric  = st.selectbox("Metric", metric_opts)

    version_opts = ["All"] + sorted(df["version_pair"].unique().tolist())
    sel_version  = st.selectbox("Version pair", version_opts)

filtered = df.copy()
if sel_status != "all":
    filtered = filtered[filtered["status"] == sel_status]
if sel_severity:
    filtered = filtered[filtered["severity"].isin(sel_severity)]
if sel_metric != "All":
    filtered = filtered[filtered["metric_id"] == sel_metric]
if sel_version != "All":
    filtered = filtered[filtered["version_pair"] == sel_version]

# ── Summary cards ─────────────────────────────────────────────────────────────

st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Total",  len(filtered))
c2.metric("Open",   int((filtered["status"] == "open").sum()))
c3.metric("Closed", int((filtered["status"] == "closed").sum()))
st.divider()

if filtered.empty:
    st.info("No regressions match the selected filters.")
    st.stop()

# ── Regression table ──────────────────────────────────────────────────────────

st.subheader("Regression details")

SEVERITY_COLORS = {"critical": "🔴", "high": "🟡", "low": "🟢", "unknown": "⚪"}
STATUS_COLORS   = {"open": "🔥", "closed": "✅"}

display_df = filtered.copy()
display_df["sev"] = display_df["severity"].map(SEVERITY_COLORS)
display_df["sts"] = display_df["status"].map(STATUS_COLORS)

col_cfg = {
    "sev":                 st.column_config.TextColumn(""),
    "sts":                 st.column_config.TextColumn(""),
    "metric_id":           st.column_config.TextColumn("Metric"),
    "screen_name":         st.column_config.TextColumn("Screen"),
    "device_cohort":       st.column_config.TextColumn("Tier"),
    "version_pair":        st.column_config.TextColumn("Version pair"),
    "baseline_p50":        st.column_config.NumberColumn("Baseline P50", format="%.2f"),
    "current_p50":         st.column_config.NumberColumn("Current P50",  format="%.2f"),
    "degradation_percent": st.column_config.NumberColumn("Degradation %", format="%.1f%%"),
    "status":              st.column_config.TextColumn("Status"),
    "detected_at":         st.column_config.DatetimeColumn("Detected", format="DD MMM YYYY"),
}

show_cols = [c for c in [
    "sev", "sts", "metric_id", "screen_name", "device_cohort", "version_pair",
    "baseline_p50", "current_p50", "degradation_percent",
    "status", "detected_at",
] if c in display_df.columns]

st.dataframe(
    display_df[show_cols].reset_index(drop=True),
    use_container_width=True,
    column_config=col_cfg,
)

# ── Status management ─────────────────────────────────────────────────────────

st.divider()
st.subheader("Update regression status")

options = {}
for _, r in filtered.iterrows():
    label = (
        f'{STATUS_COLORS.get(r["status"], "")} '
        f'{r["metric_id"]} | {r["screen_name"]} | {r["device_cohort"]} | '
        f'{r.get("version_pair", "")}'
    )
    options[label] = str(r["id"])

if not options:
    st.info("No regressions to manage.")
else:
    selected_label = st.selectbox("Select regression", list(options.keys()))
    selected_id    = options[selected_label]

    new_status = st.selectbox("New status", ["open", "closed"])

    if st.button("Apply", type="primary"):
        backend_status = "resolved" if new_status == "closed" else new_status
        ok = patch_regression(
            regression_id   = selected_id,
            project_id      = project_id,
            status          = backend_status,
            resolution_type = None,
        )
        if ok:
            st.success("Status updated.")
            st.rerun()
        else:
            st.error("Failed to update status.")

# ── Drill-down ────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Drill-down: version comparison")

drill_options = {
    f'{r["metric_id"]} | {r["screen_name"]} | {r["device_cohort"]} | {r.get("version_pair", "")}': r
    for _, r in filtered.iterrows()
}

if not drill_options:
    st.stop()

drill_label = st.selectbox("Select regression to inspect", list(drill_options.keys()),
                           key="drill_select")
drill_row   = drill_options[drill_label]

baseline_code = int(drill_row["baseline_version_code"])
current_code  = int(drill_row["current_version_code"])
metric_id     = drill_row["metric_id"]
screen_name   = drill_row["screen_name"]
device_cohort = drill_row["device_cohort"]

with st.spinner("Loading comparison data…"):
    raw_baseline = get_raw_values(project_id, metric_id, screen_name, device_cohort, baseline_code)
    raw_current  = get_raw_values(project_id, metric_id, screen_name, device_cohort, current_code)

baseline_label = f'v{drill_row["baseline_version_name"]} (baseline)'
current_label  = f'v{drill_row["current_version_name"]} (current)'

rows_ts = []
for pt in (raw_baseline or []):
    ts  = pt.get("ts") or pt.get("date")
    val = pt.get("value")
    if ts is not None and val is not None:
        rows_ts.append({"ts": ts, "value": float(val), "version": baseline_label})
for pt in (raw_current or []):
    ts  = pt.get("ts") or pt.get("date")
    val = pt.get("value")
    if ts is not None and val is not None:
        rows_ts.append({"ts": ts, "value": float(val), "version": current_label})

if rows_ts:
    ts_df = pd.DataFrame(rows_ts)
    ts_df["ts"] = pd.to_datetime(ts_df["ts"])
    fig_ts = px.line(
        ts_df.sort_values("ts"),
        x="ts",
        y="value",
        color="version",
        color_discrete_map={
            baseline_label: "#4C9BE8",
            current_label:  "#E05252",
        },
        markers=True,
        labels={"ts": "Time", "value": metric_id, "version": "Version"},
        title=f"{metric_id} over time — «{screen_name}» ({device_cohort} tier)",
    )
    fig_ts.update_layout(margin=dict(t=40, b=0))
    st.plotly_chart(fig_ts, use_container_width=True)
else:
    st.info("No raw data available yet for these versions.")
