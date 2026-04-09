import streamlit as st
from cookies import get_token
from api_client import get_me
def restore_session():
    if "token" not in st.session_state:
        token = get_token()
        if token:
            st.session_state["token"] = token

    if "token" in st.session_state and "user" not in st.session_state:
        me = get_me(st.session_state["token"])
        if me is not None:
            st.session_state["user"] = me
        else:
            # Token rejected by backend — clear session but keep the cookie
            # so a transient network error doesn't log the user out.
            for key in ["token", "user", "project_id",
                        "project_name", "package_name"]:
                st.session_state.pop(key, None)
