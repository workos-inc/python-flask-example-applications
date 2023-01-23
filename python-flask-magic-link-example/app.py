import os
import json
from flask import Flask, redirect, render_template, request, url_for
import workos
from workos import client as workos_client

# Flask Setup
DEBUG = False
app = Flask(__name__)

# WorkOS Setup
workos.api_key = os.getenv("WORKOS_API_KEY")
workos.project_id = os.getenv("WORKOS_CLIENT_ID")
workos.base_api_url = "http://localhost:5000/" if DEBUG else workos.base_api_url


def to_pretty_json(value):
    return json.dumps(value, sort_keys=True, indent=4)


app.jinja_env.filters["tojson_pretty"] = to_pretty_json


@app.route("/")
def hello_world():
    return render_template("login.html")


@app.route("/passwordless_auth", methods=["POST"])
def passwordless_auth():
    email = request.form["email"]

    session = workos_client.passwordless.create_session(
        {"email": email, "type": "MagicLink"}
    )

    # Send a custom email using your own service
    print(email, session["link"])

    # Finally, redirect to a "Check your email" page
    return render_template(
        "serve_magic_link.html", email=email, magic_link=session["link"]
    )


@app.route("/success")
def success():
    code = request.args.get("code")
    profile = workos.client.sso.get_profile_and_token(code)
    p_profile = profile.to_dict()
    raw_profile = p_profile["profile"]

    return render_template("success.html", raw_profile=raw_profile)
