# INTENTIONALLY VULNERABLE — AI / training fixture only.
from flask import Flask, make_response

app = Flask(__name__)


@app.route("/login")
def login():
    r = make_response("ok")
    r.set_cookie("session", "user=admin", secure=False, httponly=False)
    return r
