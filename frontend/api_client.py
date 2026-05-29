import os

import requests
import streamlit as st

# In Docker: API_BASE=http://perfx-backend:8080 (set via docker-compose env)
# Locally:   API_BASE=http://localhost:8080 (default)
API_BASE = os.getenv("API_BASE", "http://localhost:8080")


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


# ── Projects ──────────────────────────────────────────────────────────────────

def get_projects():
    response = requests.get(
        f"{API_BASE}/projects",
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def create_project(name: str, app_id: str):
    response = requests.post(
        f"{API_BASE}/projects",
        headers=_auth_headers(),
        json={"name": name, "package_name": app_id},
        timeout=10,
    )
    if response.status_code == 201:
        return {"status": "success", "data": response.json()}
    if response.status_code == 409:
        return {"status": "exists"}
    return {"status": "error"}


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


# ── Version releases ──────────────────────────────────────────────────────────

def get_releases(project_id: str):
    response = requests.get(
        f"{API_BASE}/releases",
        params={"project_id": project_id},
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


# ── Regressions ───────────────────────────────────────────────────────────────

def get_regressions(project_id: str, status: str | None = None):
    params = {"project_id": project_id}
    if status:
        params["status"] = status
    response = requests.get(
        f"{API_BASE}/regressions",
        params=params,
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def patch_regression(regression_id: str, project_id: str,
                     status: str | None = None,
                     resolution_type: str | None = None):
    body = {}
    if status is not None:
        body["status"] = status
    if resolution_type is not None:
        body["resolution_type"] = resolution_type

    response = requests.patch(
        f"{API_BASE}/regressions/{regression_id}",
        params={"project_id": project_id},
        json=body,
        headers=_auth_headers(),
        timeout=10,
    )
    return response.status_code == 200


# ── Metrics ───────────────────────────────────────────────────────────────────

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
            "project_id":   project_id,
            "metric_id":    metric_id,
            "screen_name":  screen_name,
            "minutes_back": minutes_back,
        },
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def get_custom_plot(project_id: str, metric_id: str, screen_name: str,
                    device_cohort: str, aggregation: str,
                    minutes_back: int, bucket_minutes: int):
    response = requests.post(
        f"{API_BASE}/projects/{project_id}/plots",
        json={
            "metric_id":     metric_id,
            "screen_name":   screen_name,
            "device_cohort": device_cohort,
            "aggregation":   aggregation,
            "minutes_back":  minutes_back,
            "bucket_minutes": bucket_minutes,
        },
        headers=_auth_headers(),
        timeout=10,
    )
    if response.status_code != 200:
        return []
    return response.json()


def get_version_compare(project_id: str, metric_id: str, screen_name: str,
                         device_cohort: str,
                         baseline_version_code: int,
                         current_version_code: int):
    response = requests.get(
        f"{API_BASE}/metrics/compare",
        params={
            "project_id":            project_id,
            "metric_id":             metric_id,
            "screen_name":           screen_name,
            "device_cohort":         device_cohort,
            "baseline_version_code": baseline_version_code,
            "current_version_code":  current_version_code,
        },
        headers=_auth_headers(),
        timeout=15,
    )
    if response.status_code != 200:
        return None
    return response.json()


def get_raw_values(project_id: str, metric_id: str, screen_name: str,
                   device_cohort: str, version_code: int):
    response = requests.get(
        f"{API_BASE}/metrics/raw-values",
        params={
            "project_id":    project_id,
            "metric_id":     metric_id,
            "screen_name":   screen_name,
            "device_cohort": device_cohort,
            "version_code":  version_code,
        },
        headers=_auth_headers(),
        timeout=15,
    )
    if response.status_code != 200:
        return []
    return response.json()
