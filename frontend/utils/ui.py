import streamlit as st


def show_page_title(title: str, subtitle: str | None = None):
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def show_error(prefix: str, error: Exception):
    st.error(f"{prefix}: {error}")