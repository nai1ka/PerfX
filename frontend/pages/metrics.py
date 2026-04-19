import streamlit as st
import pandas as pd
import plotly.express as px
from session_restore import restore_session
from menu import menu_with_redirect
from api_client import get_metric_screens, get_metric_ids, get_metrics
from utils.ui import show_error

st.set_page_config(page_title="Metrics", layout="wide")
restore_session()
menu_with_redirect()

st.title("Metrics Explorer")

project_name = st.session_state.get("project_name", "Unknown project")
project_id = st.session_state.get("project_id")
st.caption(f"Project: {project_name}")

available_screens = [""]
available_metrics = []

if project_id:
    try:
        screens = get_metric_screens(project_id)
        if screens:
            available_screens.extend(screens)

        metric_ids = get_metric_ids(project_id)
        if metric_ids:
            available_metrics.extend(metric_ids)
    except Exception as e:
        st.warning("Could not load available filters.")

if not available_metrics:
    available_metrics = ["frameTime", "cpuUsage", "memoryUsage"]

with st.form("metrics_form"):

    metric_id = st.selectbox(
        "Metric ID",
        options=available_metrics
    )

    screen_name = st.selectbox(
        "Screen Name",
        options=available_screens,
        format_func=lambda x: "All Screens" if x == "" else x
    )

    minutes_back = st.number_input(
        "Last N minutes", min_value=1, max_value=100, value=5, step=5)

    submitted = st.form_submit_button("Load metrics", width='stretch')

if submitted:
    try:
        rows = get_metrics(
            project_id=project_id,
            metric_id=metric_id,
            screen_name=screen_name,
            minutes_back=minutes_back
        )

        df = pd.DataFrame(rows)

        if df.empty:
            st.info("No metrics found.")
        else:
            chart_df = df.copy()
            chart_df["ts"] = pd.to_datetime(chart_df["ts"])

            st.subheader("Chart")
            fig = px.line(
                chart_df.sort_values("ts"),
                x="ts",
                y="value",
                color="app_version",
                title=f"{metric_id} over time"
            )
            st.plotly_chart(fig, width='stretch')

            st.subheader("Raw data")
            st.dataframe(df, width='stretch')

    except Exception as e:
        show_error("Failed to load metrics", e)
