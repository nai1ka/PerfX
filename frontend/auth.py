import streamlit as st
from cookies import save_token, clear_token

def save_login(data):
    st.session_state["token"] = data["token"]
    st.session_state["user"] = data["user"]
    save_token(data["token"])

def logout():
    # TODO remove all keys
    for key in ["token", "user", "project_id", "project_name", "package_name"]:
        if key in st.session_state:
            del st.session_state[key]
    clear_token()