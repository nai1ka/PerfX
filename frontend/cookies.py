import streamlit as st

COOKIE_NAME = "perfx_token"


def save_token(token: str) -> None:
    st.session_state["_pending_cookie"] = token


def clear_token() -> None:
    st.session_state["_pending_cookie"] = "__clear__"
