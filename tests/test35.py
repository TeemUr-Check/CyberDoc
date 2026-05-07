# INTENTIONALLY VULNERABLE — AI / training fixture only.
import sqlite3


def total(user_sort: str):
    conn = sqlite3.connect(":memory:")
    return conn.execute("SELECT SUM(price) FROM items ORDER BY " + user_sort).fetchone()
