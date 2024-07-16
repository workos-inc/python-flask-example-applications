import os
from flask import Flask, render_template, request
import workos
from workos import client as workos_client
from flask_socketio import SocketIO, emit
import json
from flask_lucide import Lucide


DEBUG = False
app = Flask(__name__)

lucide = Lucide(app)

app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

if __name__ == "__main__":
    socketio.run(app)

workos.api_key = os.getenv("WORKOS_API_KEY")
workos.base_api_url = "http://localhost:5000/" if DEBUG else workos.base_api_url
workos.client_id = os.getenv("WORKOS_CLIENT_ID")
directory_id = os.getenv("DIRECTORY_ID")


def to_pretty_json(value):
    return json.dumps(value, sort_keys=True, indent=4)


app.jinja_env.filters["tojson_pretty"] = to_pretty_json


@app.route("/")
def home():
    before = request.args.get("before")
    after = request.args.get("after")
    directories = workos.client.directory_sync.list_directories(
        before=before, after=after, limit=5, order=None
    )
    directories.list_method
    before = directories.list_metadata.before
    after = directories.list_metadata.after
    return render_template(
        "home.html", directories=directories.data, before=before, after=after
    )


@app.route("/directory")
def directory():
    directory_id = request.args.get("id")
    directory = workos.client.directory_sync.get_directory(directory_id)
    return render_template("directory.html", directory=directory.model_dump(), id=directory.id)


@app.route("/users")
def directory_users():
    directory_id = request.args.get("id")
    users = workos.client.directory_sync.list_users(
        directory=directory_id, limit=100)
    return render_template("users.html", users=users)


@app.route("/groups")
def directory_groups():
    directory_id = request.args.get("id")
    groups = workos_client.directory_sync.list_groups(
        directory=directory_id, limit=100)

    return render_template("groups.html", groups=groups)


@app.route("/webhooks", methods=["GET", "POST"])
def webhooks():
    if request.data:
        payload = request.get_data()
        sig_header = request.headers["WorkOS-Signature"]
        response = workos_client.webhooks.verify_event(
            payload=payload, sig_header=sig_header, secret=os.getenv(
                "WEBHOOKS_SECRET")
        )

        message = json.dumps(response)
        socketio.emit("webhook_received", message)

    # Return a 200 to prevent retries based on validation
    return render_template("webhooks.html")
