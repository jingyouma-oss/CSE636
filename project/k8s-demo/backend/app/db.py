"""Postgres access for the k8s-demo backend. Connection settings come from env."""
import os

import psycopg2
from psycopg2.extras import RealDictCursor


def _conn_kwargs():
    return dict(
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "appdb"),
        user=os.environ.get("DB_USER", "appuser"),
        password=os.environ.get("DB_PASSWORD", ""),
    )


def get_connection():
    return psycopg2.connect(**_conn_kwargs())


def ping():
    """Return True if the DB answers SELECT 1; raise otherwise."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        return True
    finally:
        conn.close()


def list_items():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM items ORDER BY id;")
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def add_item(name):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO items (name) VALUES (%s) RETURNING id, name;", (name,)
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row)
    finally:
        conn.close()
