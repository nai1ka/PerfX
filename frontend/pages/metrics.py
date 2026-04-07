import streamlit as st
import pandas as pd
import plotly.express as px
from session_restore import restore_session
from menu import menu_with_redirect
from services.clickhouse_service import get_clickhouse_client
from services.queries import get_metrics_query
from utils.ui import show_error

st.set_page_config(page_title="Metrics", layout="wide")
restore_session()
menu_with_redirect()

st.title("Metrics Explorer")

project_name = st.session_state.get("project_name", "Unknown project")
project_id = st.session_state.get("project_id")
st.caption(f"Project: {project_name}")

client = get_clickhouse_client()

available_screens = [""]
available_metrics = []

if project_id:
    try:
        screens_query = f"SELECT DISTINCT screen_name FROM metric_records WHERE project_id = '{project_id}' ORDER BY screen_name ASC"
        screens_df = client.query_df(screens_query)
        if not screens_df.empty:
            available_screens.extend(screens_df["screen_name"].tolist())

        metrics_query = f"SELECT DISTINCT metric_id FROM metric_records WHERE project_id = '{project_id}' ORDER BY metric_id ASC"
        metrics_df = client.query_df(metrics_query)
        if not metrics_df.empty:
            available_metrics.extend(metrics_df["metric_id"].tolist())
    except Exception as e:
        st.warning("Could not load available filters from database.")

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
        query = get_metrics_query(
            project_id=project_id,
            metric_id=metric_id,
            screen_name=screen_name,
            minutes_back=minutes_back
        )

        df = client.query_df(query)

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
