# INTENTIONALLY VULNERABLE — AI / training fixture only.
from flask import Flask, request

app = Flask(__name__)


@app.route("/welcome")
def welcome():
    name = request.args.get("name", "user")
    from flask import render_template_string

    tpl = "<h2>Welcome " + name + "</h2>"
    return render_template_string(tpl)
