# INTENTIONALLY VULNERABLE — AI / training fixture only.
from flask import Flask, request
from jinja2 import Environment, BaseLoader

app = Flask(__name__)
env = Environment(loader=BaseLoader())


@app.route("/render")
def render():
    return env.from_string(request.args.get("tpl", "")).render()
