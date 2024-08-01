import os
from flask import Flask, render_template, request
from typing_extensions import assert_never
import workos
from workos import client as workos_client
from flask_socketio import SocketIO, emit
import json
from flask_lucide import Lucide
import workos.directory_sync
import workos.resources
import workos.resources.directory_sync
import workos.typing
import workos.utils
import workos.utils.connection_types


DEBUG = False
app = Flask(__name__)

lucide = Lucide(app)

app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

if __name__ == "__main__":
    socketio.run(app)  # type: ignore

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
        before=before, after=after, limit=5
    )

    before = directories.list_metadata.before
    after = directories.list_metadata.after
    return render_template(
        "home.html", directories=directories.data, before=before, after=after
    )


@app.route("/directory")
def directory():
    directory_id = request.args.get("id")
    if not directory_id:
        return "No directory ID provided", 400
    directory = workos.client.directory_sync.get_directory(directory_id)
    
    return render_template(
        "directory.html", directory=directory.model_dump(), id=directory.id
    )


@app.route("/users")
def directory_users():
    directory_id = request.args.get("id")
    users = workos.client.directory_sync.list_users(directory=directory_id, limit=100)
    return render_template("users.html", users=users)


@app.route("/user")
def directory_user():
    user_id = request.args.get("id")
    if not user_id:
        return "No user ID provided", 400
    user = workos.client.directory_sync.get_user(user=user_id)

    return render_template("user.html", user=user.model_dump(), id=user_id)


@app.route("/groups")
def directory_groups():
    directory_id = request.args.get("id")
    groups = workos_client.directory_sync.list_groups(directory=directory_id, limit=100)

    return render_template("groups.html", groups=groups)


@app.route("/group")
def directory_group():
    group_id = request.args.get("id")
    if not group_id:
        return "No user ID provided", 400

    group = workos_client.directory_sync.get_group(group=group_id)

    return render_template("group.html", group=group.model_dump(), id=group_id)


@app.route("/events")
def events():
    after = request.args.get("after")
    events = workos.client.events.list_events(
        events=[
            "dsync.activated",
            "dsync.deleted",
            "dsync.group.created",
            "dsync.group.deleted",
            "dsync.group.updated",
            "dsync.user.created",
            "dsync.user.deleted",
            "dsync.user.updated",
            "dsync.group.user_added",
            "dsync.group.user_removed",
        ],
        after=after,
        limit=20,
    )

    after = events.list_metadata.after
    events_data = list(map(lambda event: event.model_dump(), events.data))
    return render_template("events.html", events=events_data, after=after)


@app.route("/webhooks", methods=["GET", "POST"])
def webhooks():
    signing_secret = os.getenv("WEBHOOKS_SECRET")
    if request.data:
        if signing_secret:
            payload = request.get_data()
            sig_header = request.headers["WorkOS-Signature"]
            response = workos_client.webhooks.verify_event(
                payload=payload, sig_header=sig_header, secret=signing_secret
            )
            message = json.dumps(response.dict())
            socketio.emit("webhook_received", message)
        else:
            print("No signing secret configured")

    # Return a 200 to prevent retries based on validation
    return render_template("webhooks.html")
