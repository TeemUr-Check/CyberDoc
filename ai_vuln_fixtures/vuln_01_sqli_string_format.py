# INTENTIONALLY VULNERABLE — AI / training fixture only. Do not use in production.
import sqlite3

def lookup_user(username: str):
    conn = sqlite3.connect("app.db")
    q = "SELECT * FROM users WHERE name = '" + username + "'"
    return conn.execute(q).fetchall()
