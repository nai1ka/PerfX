import streamlit as st
from services.clickhouse_service import get_clickhouse_client
from services.queries import (
    get_dashboard_counts_query,
    get_latest_regressions_count_query,
)
from session_restore import restore_session
from menu import menu_with_redirect
from utils.ui import show_page_title, show_error

show_page_title("Dashboard", "Overview of collected metrics and regressions")
restore_session()
menu_with_redirect()
client = get_clickhouse_client()

col1, col2 = st.columns(2)

try:
    total_rows_df = client.query_df(get_dashboard_counts_query())
    total_rows = int(total_rows_df.iloc[0]["total_rows"]) if not total_rows_df.empty else 0
except Exception as e:
    total_rows = None
    show_error("Failed to load total metric count", e)

try:
    regressions_df = client.query_df(get_latest_regressions_count_query())
    regressions_count = int(regressions_df.iloc[0]["regressions_count"]) if not regressions_df.empty else 0
except Exception as e:
    regressions_count = None
    show_error("Failed to load regressions count", e)

with col1:
    st.metric("Total metric rows", total_rows if total_rows is not None else "N/A")

with col2:
    st.metric("Detected regressions", regressions_count if regressions_count is not None else "N/A")