import extra_streamlit_components as stx
import streamlit as st

COOKIE_NAME = "perfx_token"

# Used only for write operations (set / delete).
# Reading is done via st.context.cookies which is available on every render
# without requiring a component round-trip.
_writer = stx.CookieManager(key="perfx_cookie_writer")


def save_token(token: str) -> None:
    _writer.set(COOKIE_NAME, token)


def get_token() -> str | None:
    return st.context.cookies.get(COOKIE_NAME)


def clear_token() -> None:
    _writer.delete(COOKIE_NAME)
