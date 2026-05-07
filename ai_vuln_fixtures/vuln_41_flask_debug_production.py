# INTENTIONALLY VULNERABLE — AI / training fixture only.
from flask import Flask

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "dev"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
