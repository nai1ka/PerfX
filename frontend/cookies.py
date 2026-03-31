import streamlit as st
import extra_streamlit_components as stx

COOKIE_NAME = "perfx_token"


cookie_manager = stx.CookieManager(key="perfx_cookie_manager")


def save_token(token: str):
    cookie_manager.set(COOKIE_NAME, token)


def get_token():
    return cookie_manager.get(COOKIE_NAME)


def clear_token():
    cookie_manager.delete(COOKIE_NAME)
