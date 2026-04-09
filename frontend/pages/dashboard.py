import plotly.express as px
import streamlit as st

from menu import menu_with_redirect
from services.clickhouse_service import get_clickhouse_client
from services.postgres_service import fetch_regressions
from services.queries import (
    get_project_status_query,
    get_project_metrics_query,
    get_custom_plot_query,
)
from session_restore import restore_session
from utils.ui import show_error, show_page_title

show_page_title("Dashboard", "System status and custom plots")
restore_session()
menu_with_redirect()

project_id = st.session_state.get("project_id")
project_name = st.session_state.get("project_name", "—")

if not project_id:
    st.info("Select a project from the sidebar to continue.")
    st.stop()

ch = get_clickhouse_client()

# ── System status ─────────────────────────────────────────────────────────────

st.subheader("System status")

c1, c2, c3, c4, c5 = st.columns(5)

try:
    status_df = ch.query_df(get_project_status_query(project_id))
    row = status_df.iloc[0] if not status_df.empty else None
    total_rows = int(row["total_rows"]) if row is not None else 0
    last_ingested = (
        row["last_ingested"].strftime("%d %b %Y %H:%M")
        if row is not None and row["last_ingested"] is not None
        else "—"
    )
    unique_metrics = int(row["unique_metrics"]) if row is not None else 0
    unique_screens = int(row["unique_screens"]) if row is not None else 0
except Exception as e:
    total_rows = unique_metrics = unique_screens = None
    last_ingested = "error"
    show_error("ClickHouse status unavailable", e)

try:
    regressions = fetch_regressions(project_id=project_id)
    regression_count = len(regressions)
    last_regression = (
        regressions[0]["detected_at"].strftime("%d %b %Y %H:%M")
        if regressions else "—"
    )
except Exception as e:
    regression_count = None
    last_regression = "error"
    show_error("PostgreSQL status unavailable", e)

c1.metric("Metric rows", total_rows if total_rows is not None else "N/A")
c2.metric("Last ingested", last_ingested)
c3.metric("Unique metrics", unique_metrics if unique_metrics is not None else "N/A")
c4.metric("Unique screens", unique_screens if unique_screens is not None else "N/A")
c5.metric("Regressions", regression_count if regression_count is not None else "N/A")

st.divider()

# ── Load available dimensions for plot builder ────────────────────────────────

try:
    dims_df = ch.query_df(get_project_metrics_query(project_id))
    has_dims = not dims_df.empty
except Exception as e:
    dims_df = None
    has_dims = False
    show_error("Could not load metric dimensions", e)

# ── Custom plots ──────────────────────────────────────────────────────────────

st.subheader("Custom plots")

if "dashboard_plots" not in st.session_state:
    st.session_state["dashboard_plots"] = []

plots: list[dict] = st.session_state["dashboard_plots"]

# Add plot form
with st.expander("Add plot", expanded=not plots):
    if not has_dims:
        st.info("No metric data available for this project yet.")
    else:
        metrics = sorted(dims_df["metric_id"].unique().tolist())
        screens = sorted(dims_df["screen_name"].unique().tolist())
        cohorts = ["All"] + sorted(dims_df["device_cohort"].unique().tolist())

        fa, fb, fc = st.columns(3)
        with fa:
            new_metric = st.selectbox("Metric", metrics, key="np_metric")
        with fb:
            new_screen = st.selectbox("Screen", screens, key="np_screen")
        with fc:
            new_cohort = st.selectbox(
                "Device cohort", cohorts, key="np_cohort"
            )

        fd, fe, ff = st.columns(3)
        with fd:
            new_agg = st.selectbox(
                "Aggregation", ["P95", "P50", "Avg", "Max"], key="np_agg"
            )
        with fe:
            new_window = st.selectbox(
                "Time window",
                [30, 60, 120, 360, 720, 1440],
                format_func=lambda m: (
                    f"{m} min" if m < 60 else f"{m // 60} h"
                ),
                key="np_window",
            )
        with ff:
            new_bucket = st.selectbox(
                "Bucket size",
                [1, 5, 10, 30, 60],
                format_func=lambda m: f"{m} min",
                key="np_bucket",
            )

        if st.button("Add plot"):
            plots.append({
                "metric_id": new_metric,
                "screen_name": new_screen,
                "device_cohort": new_cohort,
                "aggregation": new_agg,
                "minutes_back": new_window,
                "bucket_minutes": new_bucket,
            })
            st.rerun()

# Render plots
if not plots:
    st.info("No plots added yet. Use the form above to add one.")
else:
    for i, plot in enumerate(plots):
        label = (
            f"{plot['aggregation']} {plot['metric_id']} "
            f"/ {plot['screen_name']}"
            + (
                f" / {plot['device_cohort']}"
                if plot["device_cohort"] != "All" else ""
            )
            + f"  —  last "
            + (
                f"{plot['minutes_back']} min"
                if plot["minutes_back"] < 60
                else f"{plot['minutes_back'] // 60} h"
            )
        )

        col_title, col_remove = st.columns([10, 1])
        with col_title:
            st.markdown(f"**{label}**")
        with col_remove:
            if st.button("✕", key=f"rm_{i}"):
                plots.pop(i)
                st.rerun()

        try:
            df = ch.query_df(get_custom_plot_query(
                project_id=project_id,
                metric_id=plot["metric_id"],
                screen_name=plot["screen_name"],
                device_cohort=plot["device_cohort"],
                minutes_back=plot["minutes_back"],
                aggregation=plot["aggregation"],
                bucket_minutes=plot["bucket_minutes"],
            ))
            if df.empty:
                st.caption("No data for this combination.")
            else:
                fig = px.line(
                    df,
                    x="bucket",
                    y="metric_value",
                    labels={
                        "bucket": "Time",
                        "metric_value": plot["aggregation"],
                    },
                )
                fig.update_layout(margin=dict(t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            show_error("Failed to load plot data", e)
