import requests
import streamlit as st

API_BASE = "http://185.71.196.185:8080"


def login(email: str, password: str):
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    if response.status_code != 200:
        return None
    return response.json()


def signup(email: str, password: str):
    response = requests.post(
        f"{API_BASE}/auth/signup",
        json={"email": email, "password": password},
        timeout=10,
    )
    if response.status_code != 201:
        return None
    return response.json()


def get_projects():
    token = st.session_state.get("token")
    if not token:
        return []

    response = requests.get(
        f"{API_BASE}/projects",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if response.status_code != 200:
        return []

    return response.json()


def create_project(name: str, app_id: str):
    token = st.session_state.get("token")

    response = requests.post(
        f"{API_BASE}/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "package_name": app_id
        },
        timeout=10,
    )

    if response.status_code == 201:
        return {"status": "success", "data": response.json()}

    if response.status_code == 409:
        return {"status": "exists"}

    return {"status": "error"}

def get_me(token: str):
    response = requests.get(
        f"{API_BASE}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if response.status_code != 200:
        return None
    return response.json()
