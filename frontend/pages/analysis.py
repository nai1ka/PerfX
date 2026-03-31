import streamlit as st
from services.clickhouse_service import get_clickhouse_client
from services.queries import (
    get_regressions_query,
    get_thresholds_query,
)
from session_restore import restore_session
from menu import menu_with_redirect
from utils.ui import show_page_title, show_error

show_page_title("Analysis", "Regression detection and alert thresholds")
restore_session()
menu_with_redirect()
client = get_clickhouse_client()

st.subheader("Detected regressions")

try:
    regressions_df = client.query_df(get_regressions_query())

    if regressions_df.empty:
        st.info("No regressions detected.")
    else:
        st.dataframe(regressions_df, width="stretch")

except Exception as e:
    show_error("Failed to load regressions", e)

st.divider()

st.subheader("Threshold configuration")

try:
    thresholds_df = client.query_df(get_thresholds_query())

    if thresholds_df.empty:
        st.info("No thresholds configured.")
    else:
        st.dataframe(thresholds_df, width="stretch")

except Exception as e:
    show_error("Failed to load thresholds", e)

st.divider()

st.subheader("Add / update threshold")

app_id = st.text_input("App ID")
metric_id = st.text_input("Metric ID", value="frame_time")
screen_name = st.text_input("Screen name")
device_cohort = st.text_input("Device cohort")

p50_threshold = st.number_input("P50 threshold", value=0.10)
p95_threshold = st.number_input("P95 threshold", value=0.20)
p_value_threshold = st.number_input("P-value threshold", value=0.05)

if st.button("Save threshold"):
    try:
        insert_query = f"""
        INSERT INTO alert_thresholds
        (
            app_id,
            metric_id,
            screen_name,
            device_cohort,
            p50_threshold,
            p95_threshold,
            p_value_threshold
        )
        VALUES
        (
            '{app_id}',
            '{metric_id}',
            '{screen_name}',
            '{device_cohort}',
            {p50_threshold},
            {p95_threshold},
            {p_value_threshold}
        )
        """

        client.command(insert_query)

        st.success("Threshold saved")

    except Exception as e:
        show_error("Failed to save threshold", e)