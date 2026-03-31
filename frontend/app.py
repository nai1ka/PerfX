import streamlit as st

from api_client import login, signup, get_me
from auth import save_login, logout
from cookies import get_token
from menu import menu
from session_restore import restore_session

st.set_page_config(page_title="PerfX", layout="wide")

restore_session()
menu()

st.title("PerfX")

# Logged-in state
user = st.session_state.get("user")
if user is not None:
    # st.success(f"Logged in as {user['email']}")
    # st.info("Use the sidebar to open Dashboard, Metrics, Analysis, or Projects.")
    st.switch_page("pages/dashboard.py")


# Login / Signup UI
tab_login, tab_signup = st.tabs(["Login", "Signup"])

with tab_login:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", width="stretch"):
        result = login(email, password)
        if result is None:
            st.error("Invalid credentials")
        else:
            save_login(result)
            st.switch_page("pages/metrics.py")

with tab_signup:
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm = st.text_input("Confirm password", type="password", key="signup_confirm")

    if st.button("Create account", width="stretch"):
        if password != confirm:
            st.error("Passwords do not match")
        else:
            result = signup(email, password)
            if result is None:
                st.error("Signup failed")
            else:
                save_login(result)
                st.switch_page("pages/dashboard.py")