import os
import json
from flask import Flask, render_template, request
import workos

# Flask Setup
DEBUG = False
app = Flask(__name__)

# WorkOS Setup
base_api_url = "http://localhost:7000/" if DEBUG else None
workos_client = workos.WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID"),
    base_url=base_api_url,
)

redirect_uri = "http://localhost:5000/success"


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
        email=email, type="MagicLink", redirect_uri=redirect_uri
    )

    # Send a custom email using your own service
    print(email, session.link)

    # Finally, redirect to a "Check your email" page
    return render_template(
        "serve_magic_link.html", email=email, magic_link=session.link
    )


@app.route("/success")
def success():
    code = request.args.get("code")
    if not code:
        return "No code provided"
    profile = workos_client.sso.get_profile_and_token(code)

    return render_template("success.html", raw_profile=profile.dict())
