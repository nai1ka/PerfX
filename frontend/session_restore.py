import streamlit as st
from streamlit_cookies_manager import CookieManager

from api_client import get_me
from cookies import COOKIE_NAME


def _get_cookies() -> CookieManager:
    cookies = CookieManager()
    if not cookies.ready():
        # Block until the browser sends its cookies back via the component.
        # This causes one silent extra render on the very first page load.
        st.stop()
    return cookies


def restore_session() -> None:
    cookies = _get_cookies()

    # Process any pending cookie write/clear from the previous interaction.
    pending = st.session_state.pop("_pending_cookie", None)
    if pending == "__clear__":
        if COOKIE_NAME in cookies:
            del cookies[COOKIE_NAME]
            cookies.save()
    elif pending is not None:
        cookies[COOKIE_NAME] = pending
        cookies.save()
        # Rerun so the browser has a cycle to commit the cookie before we
        # redirect.  On the next run _pending_cookie is gone and we redirect.
        st.rerun()

    # Restore token + user from cookie on a fresh session (after F5 refresh).
    if "token" not in st.session_state:
        token = cookies.get(COOKIE_NAME)
        if token:
            st.session_state["token"] = token

    if "token" in st.session_state and "user" not in st.session_state:
        me = get_me(st.session_state["token"])
        if me is not None:
            st.session_state["user"] = me
        else:
            for key in ["token", "user", "project_id", "project_name", "package_name"]:
                st.session_state.pop(key, None)
