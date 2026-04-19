import requests
import streamlit as st

API_BASE = "http://localhost:8080"


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


def _auth_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def get_regressions(project_id: str):
    response = requests.get(
        f"{API_BASE}/regressions",
        params={"project_id": project_id},
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def delete_regression(regression_id: str, project_id: str):
    response = requests.delete(
        f"{API_BASE}/regressions/{regression_id}",
        params={"project_id": project_id},
        headers=_auth_headers(),
        timeout=10,
    )
    return response.status_code == 200


def get_metric_screens(project_id: str):
    response = requests.get(
        f"{API_BASE}/metrics/screens",
        params={"project_id": project_id},
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def get_metric_ids(project_id: str):
    response = requests.get(
        f"{API_BASE}/metrics/metric-ids",
        params={"project_id": project_id},
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def get_metrics(project_id: str, metric_id: str, screen_name: str, minutes_back: int):
    response = requests.get(
        f"{API_BASE}/metrics",
        params={
            "project_id": project_id,
            "metric_id": metric_id,
            "screen_name": screen_name,
            "minutes_back": minutes_back,
        },
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def get_project_status(project_id: str):
    response = requests.get(
        f"{API_BASE}/projects/{project_id}/status",
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return None
    return response.json()


def get_project_dimensions(project_id: str):
    response = requests.get(
        f"{API_BASE}/projects/{project_id}/dimensions",
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def get_custom_plot(project_id: str, metric_id: str, screen_name: str,
                    device_cohort: str, aggregation: str, minutes_back: int,
                    bucket_minutes: int):
    response = requests.post(
        f"{API_BASE}/projects/{project_id}/plots",
        json={
            "metric_id": metric_id,
            "screen_name": screen_name,
            "device_cohort": device_cohort,
            "aggregation": aggregation,
            "minutes_back": minutes_back,
            "bucket_minutes": bucket_minutes,
        },
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()
