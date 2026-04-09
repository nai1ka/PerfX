import streamlit as st
from clickhouse_connect import get_client


@st.cache_resource
def get_clickhouse_client():
    return get_client(
        host="localhost",
        port=8123,
        username="metrics_user",
        password="metrics_pass",
        database="metrics",
    )