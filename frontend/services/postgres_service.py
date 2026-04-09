import psycopg2
import psycopg2.extras
import streamlit as st


@st.cache_resource
def get_postgres_conn():
    return psycopg2.connect(
        host="localhost",
        dbname="perfx",
        user="perfx_user",
        password="perfx_pass",
    )


def fetch_regressions(project_id: str | None = None) -> list[dict]:
    conn = get_postgres_conn()
    query = """
        SELECT
            r.id,
            p.name        AS project_name,
            r.metric_id,
            r.screen_name,
            r.device_cohort,
            r.baseline_p95,
            r.current_p95,
            r.degradation_percent,
            r.p_value,
            r.detected_at
        FROM regressions r
        JOIN projects p ON p.id = r.project_id
        {where}
        ORDER BY r.detected_at DESC
        LIMIT 200
    """
    where = ""
    params: tuple = ()
    if project_id:
        where = "WHERE r.project_id = %s"
        params = (project_id,)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query.format(where=where), params)
        return cur.fetchall()


def delete_regression(regression_id: str) -> None:
    conn = get_postgres_conn()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM regressions WHERE id = %s",
            (regression_id,),
        )
    conn.commit()
