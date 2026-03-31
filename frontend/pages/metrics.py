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
st.caption(f"Project: {project_name}")

client = get_clickhouse_client()

# You can later replace this with project → app_id mapping from backend
default_app_id = "com.ndevelop.perfx"

with st.form("metrics_form"):
    metric_id = st.text_input("Metric ID", value="frameTime")
    screen_name = st.text_input("Screen Name", value="")
    limit = st.number_input("Max rows", min_value=100, max_value=50000, value=5000, step=100)

    submitted = st.form_submit_button("Load metrics", width="stretch")

if submitted:
    try:
        query = get_metrics_query(
            # TODO fix when package name doest exists
            package_name=st.session_state["package_name"],
            metric_id=metric_id,
            screen_name=screen_name,
            limit=limit,
        )

        df = client.query_df(query)

        if df.empty:
            st.info("No metrics found.")
        else:
            st.subheader("Raw data")
            st.dataframe(df, width="stretch")

            chart_df = df.copy()
            chart_df["ts"] = pd.to_datetime(chart_df["ts"])

            st.subheader("Chart")
            fig = px.line(
                chart_df.sort_values("ts"),
                x="ts",
                y="value",
                color="app_version",
                title="Metric values over time"
            )
            st.plotly_chart(fig, width="stretch")

    except Exception as e:
        show_error("Failed to load metrics", e)