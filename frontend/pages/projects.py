import streamlit as st
import pandas as pd
from session_restore import restore_session
from menu import menu_with_redirect
from api_client import get_projects, create_project

st.set_page_config(page_title="Projects", layout="wide")
restore_session()
menu_with_redirect()

st.title("Projects")
st.caption("Create and manage your Android applications")

st.subheader("Create new project")

with st.form("create_project_form"):
    project_name = st.text_input("Project name")
    app_id = st.text_input(
        "Android App ID",
        placeholder="com.example.app"
    )

    submitted = st.form_submit_button("Create project", width="stretch")

if submitted:

    if not project_name.strip():
        st.error("Project name is required")

    elif not app_id.strip():
        st.error("Android App ID is required")

    else:
        result = create_project(
            name=project_name.strip(),
            app_id=app_id.strip(),
        )

        if result["status"] == "exists":
            st.error("Project with this name or App ID already exists")

        elif result["status"] == "error":
            st.error("Failed to create project")

        else:
            project = result["data"]
            st.success("Project created successfully")
            st.write("Use this identifier in your Android SDK:")
            st.code(project["id"])
            st.session_state["project_id"] = project["id"]

st.divider()

st.subheader("Existing projects")

projects = get_projects()

if not projects:
    st.info("No projects found.")
else:
    df = pd.DataFrame(projects)
    st.dataframe(df, width="stretch")