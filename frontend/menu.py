import streamlit as st
from auth import logout
from api_client import get_projects


def _is_logged_in():
    return "token" in st.session_state and "user" in st.session_state


def unauthenticated_menu():
    st.sidebar.page_link("app.py", label="Login", icon="🔐")


def authenticated_menu():
    user = st.session_state["user"]

    st.sidebar.markdown("## User")
    st.sidebar.write(user["email"])

    if st.sidebar.button("Logout", width="stretch"):
        logout()
        st.switch_page("app.py")

    st.sidebar.divider()

    projects = get_projects()
    if not projects:
        st.sidebar.warning("No projects available")
    else:
        project_names = {p["name"]: p["id"] for p in projects}
        project_labels = list(project_names.keys())

        current_project_name = st.session_state.get("project_name")
        if current_project_name not in project_labels:
            current_project_name = project_labels[0]

        selected_project_name = st.sidebar.selectbox(
            "Project",
            project_labels,
            index=project_labels.index(current_project_name),
        )

        selected_project = next(
            (p for p in projects if p["name"] == selected_project_name), None)

        st.session_state["project_name"] = selected_project_name
        st.session_state["project_id"] = project_names[selected_project_name]

# TODO ???
        if selected_project is not None:
            st.session_state["package_name"] = selected_project["package_name"]

    st.sidebar.divider()
    st.sidebar.markdown("## Navigation")

    st.sidebar.page_link(
        "pages/dashboard.py",
        label="Dashboard",
        icon="📊",
    )
    st.sidebar.page_link(
        "pages/metrics.py",
        label="Metrics",
        icon="📈",
    )
    st.sidebar.page_link(
        "pages/analysis.py",
        label="Analysis",
        icon="🧪",
    )
    st.sidebar.page_link(
        "pages/projects.py",
        label="Projects",
        icon="📁",
    )


def menu():
    if not _is_logged_in():
        unauthenticated_menu()
        return

    authenticated_menu()


def menu_with_redirect():
    if not _is_logged_in():
        st.switch_page("app.py")

    authenticated_menu()
