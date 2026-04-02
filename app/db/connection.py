"""Conexão com Postgres — usa variáveis de ambiente."""
import os
import psycopg2


def get_conn():
    """Retorna nova conexão com o Postgres."""
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "tracking"),
        user=os.getenv("DB_USER", "tracker"),
        password=os.getenv("DB_PASS", "adminforte"),
        host=os.getenv("DB_HOST", "db"),
        connect_timeout=5,
    )
