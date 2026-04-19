import pandas as pd
import plotly.express as px
import streamlit as st

from menu import menu_with_redirect
from api_client import get_regressions, delete_regression
from session_restore import restore_session
from utils.ui import show_error, show_page_title

show_page_title("Analysis", "Detected performance regressions")
restore_session()
menu_with_redirect()

# ── Load data ─────────────────────────────────────────────────────────────────

project_id = st.session_state.get("project_id")

try:
    rows = get_regressions(project_id=project_id)
except Exception as e:
    show_error("Failed to load regressions", e)
    st.stop()

if not rows:
    st.info("No regressions detected yet.")
    st.stop()

df = pd.DataFrame(rows)
df["detected_at"] = pd.to_datetime(df["detected_at"], utc=True)
df["degradation_percent"] = df["degradation_percent"].round(1)
df["p_value"] = df["p_value"].round(4)

# ── Filters ───────────────────────────────────────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    projects = ["All"] + sorted(df["project_name"].unique().tolist())
    selected_project = st.selectbox("Project", projects)

with col2:
    metrics = ["All"] + sorted(df["metric_id"].unique().tolist())
    selected_metric = st.selectbox("Metric", metrics)

filtered = df.copy()
if selected_project != "All":
    filtered = filtered[filtered["project_name"] == selected_project]
if selected_metric != "All":
    filtered = filtered[filtered["metric_id"] == selected_metric]

# ── Summary cards ─────────────────────────────────────────────────────────────

st.divider()

c1, c2, c3 = st.columns(3)
c1.metric("Total regressions", len(filtered))
avg_deg = (
    f'{filtered["degradation_percent"].mean():.1f}%'
    if not filtered.empty else "—"
)
worst_deg = (
    f'{filtered["degradation_percent"].max():.1f}%'
    if not filtered.empty else "—"
)
c2.metric("Avg degradation", avg_deg)
c3.metric("Worst degradation", worst_deg)

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────

if filtered.empty:
    st.info("No regressions match the selected filters.")
    st.stop()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Regressions over time")
    timeline = (
        filtered.set_index("detected_at")
        .resample("1h")
        .size()
        .reset_index(name="count")
    )
    fig_time = px.bar(
        timeline,
        x="detected_at",
        y="count",
        labels={"detected_at": "Time", "count": "Regressions"},
    )
    fig_time.update_layout(margin=dict(t=20, b=0))
    st.plotly_chart(fig_time, use_container_width=True)

with col_right:
    st.subheader("Degradation by metric")
    fig_box = px.box(
        filtered,
        x="metric_id",
        y="degradation_percent",
        color="device_cohort",
        labels={
            "metric_id": "Metric",
            "degradation_percent": "Degradation %",
            "device_cohort": "Device tier",
        },
    )
    fig_box.update_layout(margin=dict(t=20, b=0))
    st.plotly_chart(fig_box, use_container_width=True)

# ── Regression table ──────────────────────────────────────────────────────────

st.subheader("Regression details")

display_cols = [
    "project_name", "metric_id", "screen_name", "device_cohort",
    "baseline_p95", "current_p95", "degradation_percent", "p_value",
    "detected_at",
]

col_cfg = {
    "project_name": st.column_config.TextColumn("Project"),
    "metric_id": st.column_config.TextColumn("Metric"),
    "screen_name": st.column_config.TextColumn("Screen"),
    "device_cohort": st.column_config.TextColumn("Device tier"),
    "baseline_p95": st.column_config.NumberColumn(
        "Baseline P95", format="%.2f"
    ),
    "current_p95": st.column_config.NumberColumn(
        "Current P95", format="%.2f"
    ),
    "degradation_percent": st.column_config.NumberColumn(
        "Degradation %", format="%.1f%%"
    ),
    "p_value": st.column_config.NumberColumn("p-value", format="%.4f"),
    "detected_at": st.column_config.DatetimeColumn(
        "Detected at", format="DD MMM YYYY, HH:mm"
    ),
}

st.dataframe(
    filtered[display_cols].reset_index(drop=True),
    use_container_width=True,
    column_config=col_cfg,
)

# ── Delete regressions ────────────────────────────────────────────────────────

st.divider()
st.subheader("Delete regression")

options = {
    (
        f'{r["metric_id"]} | {r["screen_name"]} | '
        f'{r["device_cohort"]} ({r["degradation_percent"]:.1f}%)'
    ): str(r["id"])
    for _, r in filtered.iterrows()
}

selected_label = st.selectbox("Select regression", list(options.keys()))

if st.button("Delete", type="primary"):
    try:
        delete_regression(options[selected_label], project_id)
        st.success("Regression deleted.")
        st.rerun()
    except Exception as e:
        show_error("Failed to delete regression", e)
