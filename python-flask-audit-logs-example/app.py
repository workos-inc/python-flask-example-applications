import json
import os
from flask import Flask, session, redirect, render_template, request
import workos
from datetime import datetime, timedelta
from audit_log_events import (
    user_organization_set,
)
from workos.audit_logs import AuditLogEvent
from flask_lucide import Lucide


# Flask Setup
DEBUG = False
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

lucide = Lucide(app)


# WorkOS Setup
base_api_url = "http://localhost:7000/" if DEBUG else None
workos_client = workos.WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID"),
    base_url=base_api_url,
)


def to_pretty_json(value):
    return json.dumps(value, sort_keys=True, indent=4)


app.jinja_env.filters["tojson_pretty"] = to_pretty_json


@app.route("/", methods=["POST", "GET"])
def index():
    try:
        link = workos_client.portal.generate_link(
            organization_id=session["organization_id"], intent="audit_logs"
        )
        today = datetime.today()
        last_month = today - timedelta(days=30)
        return render_template(
            "send_events.html",
            link=link.link,
            organization_id=session["organization_id"],
            org_name=session["organization_name"],
            last_month_iso=last_month.isoformat(),
            today_iso=today.isoformat(),
        )
    except KeyError:
        before = request.args.get("before")
        after = request.args.get("after")
        organizations = workos_client.organizations.list_organizations(
            before=before, after=after, limit=5, order="desc"
        )
        before = organizations.list_metadata.before
        after = organizations.list_metadata.after
        return render_template(
            "login.html",
            organizations=organizations.data,
            before=before,
            after=after,
        )


@app.route("/set_org", methods=["POST", "GET"])
def set_org():
    organization_id = request.args.get("id") or request.form["organization_id"]

    session["organization_id"] = organization_id
    workos_client.audit_logs.create_event(
        organization_id=organization_id, event=user_organization_set
    )
    org = workos_client.organizations.get_organization(organization_id)
    session["organization_name"] = org.name
    return redirect("/")


@app.route("/send_event", methods=["POST", "GET"])
def send_event():
    event_version, actor_name, actor_type, target_name, target_type = (
        request.form["event-version"],
        request.form["actor-name"],
        request.form["actor-type"],
        request.form["target-name"],
        request.form["target-type"],
    )
    organization_id = session["organization_id"]

    event = AuditLogEvent(
        {
            "action": "user.organization_deleted",
            "version": int(event_version),
            "occurred_at": datetime.now().isoformat(),
            "actor": {
                "type": actor_type,
                "name": actor_name,
                "id": "user_01GBNJC3MX9ZZJW1FSTF4C5938",
            },
            "targets": [
                {
                    "type": target_type,
                    "name": target_name,
                    "id": "team_01GBNJD4MKHVKJGEWK42JNMBGS",
                },
            ],
            "context": {
                "location": "123.123.123.123",
                "user_agent": "Chrome/104.0.0.0",
            },
        }
    )
    organization_set = workos_client.audit_logs.create_event(
        organization_id=organization_id, event=event
    )
    return redirect("/")


@app.route("/export_events", methods=["POST", "GET"])
def export_events():
    today = datetime.today()
    last_month = today - timedelta(days=30)
    organization_id = session["organization_id"]
    return render_template(
        "send_events.html",
        organization_id=organization_id,
        org_name=session["organization_name"],
        last_month_iso=last_month.isoformat(),
        today_iso=today.isoformat(),
    )


@app.route("/get_events", methods=["POST", "GET"])
def get_events():
    organization_id = session["organization_id"]
    event_type = request.form["event"]

    if event_type == "generate_csv":
        if request.form["filter-actions"] != "":
            actions = request.form["filter-actions"]
        else:
            actions = None
        if request.form["filter-actors"] != "":
            actors = request.form["filter-actors"]
        else:
            actors = None
        if request.form["filter-targets"] != "":
            targets = request.form["filter-targets"]
        else:
            targets = None

        try:

            create_export_response = workos_client.audit_logs.create_export(
                organization_id=organization_id,
                range_start=request.form["range-start"],
                range_end=request.form["range-end"],
                actions=actions,
                actor_names=actors,
                targets=targets,
            )
            session["export_id"] = create_export_response.id

            return redirect("export_events")
        except Exception as e:
            print(str(e))
            return redirect("/")
    if event_type == "access_csv":
        export_id = session["export_id"]
        fetch_export_response = workos_client.audit_logs.get_export(export_id)
        if fetch_export_response.url is None:
            return redirect("/")

        return redirect(fetch_export_response.url)


@app.route("/events", methods=["GET"])
def events():
    intent = request.args.get("intent")
    if not intent == "audit_logs":
        return redirect("/")

    link = workos_client.portal.generate_link(
        organization_id=session["organization_id"], intent=intent
    )

    return redirect(link.link)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
