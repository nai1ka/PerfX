import clickhouse_connect
import psycopg2

from .config import (
    CH_HOST, CH_PORT, CH_USER, CH_PASSWORD, CH_DATABASE,
    PG_HOST, PG_DB, PG_USER, PG_PASSWORD,
)


def get_ch_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        port=CH_PORT,
        username=CH_USER,
        password=CH_PASSWORD,
        database=CH_DATABASE,
    )


def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )
