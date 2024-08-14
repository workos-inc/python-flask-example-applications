from email.mime import base
import os
from flask import Flask, redirect, render_template, request
import workos
from flask_lucide import Lucide
from workos.types import DomainDataInput


# Flask Setup
app = Flask(__name__)
lucide = Lucide(app)

# WorkOS Setup
base_api_url = os.getenv("WORKOS_BASE_API_URL")
workos_client = workos.WorkOSClient(
    api_key=os.getenv("WORKOS_API_KEY"),
    client_id=os.getenv("WORKOS_CLIENT_ID"),
    base_url=base_api_url,
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/provision_enterprise", methods=["POST"])
def provision_enterprise():
    # Create global variable for org_id
    global org_id
    organization_name = request.form["org"]
    organization_domains = request.form["domain"].split()

    # Check if a matching domain already exists and set global org_id if there is a match
    orgs = workos_client.organizations.list_organizations(domains=organization_domains)
    if len(orgs.data) > 0:
        org_id = orgs.data[0].id

    # Otherwise create a new Organization and set the global org_id
    else:
        domain_data = list(
            map(
                lambda domain: DomainDataInput(domain=domain, state="verified"),
                organization_domains,
            )
        )

        organization = workos_client.organizations.create_organization(
            name=organization_name,
            domain_data=domain_data,
        )
        org_id = organization.id

    return render_template("org_logged_in.html")


@app.route("/launch_admin_portal", methods=["GET", "POST"])
def launch_admin_portal():
    intent = request.args.get("intent")

    if intent is None:
        return "Missing intent parameter", 400

    if not intent in tuple(("audit_logs", "dsync", "log_streams", "sso")):
        return "Invalid intent parameter", 400

    portal_link = workos_client.portal.generate_link(
        organization_id=org_id, intent=intent
    )
    return redirect(portal_link.link)
