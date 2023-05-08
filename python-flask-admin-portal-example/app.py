import os

from flask import Flask, redirect, render_template, request, url_for
import workos
from workos import client as workos_client
from workos import portal
from flask_lucide import Lucide


# Flask Setup
DEBUG = False
app = Flask(__name__)
lucide = Lucide(app)

# WorkOS Setup
workos.api_key = os.getenv("WORKOS_API_KEY")
workos.project_id = os.getenv("WORKOS_CLIENT_ID")
workos.base_api_url = "http://localhost:7000/" if DEBUG else workos.base_api_url


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
    if len(orgs["data"]) > 0:
        org_id = orgs["data"][0]["id"]

    # Otherwise create a new Organization and set the global org_id
    else:
        organization = workos_client.organizations.create_organization(
            {"name": organization_name, "domains": organization_domains}
        )
        org_id = organization["id"]

    return render_template("org_logged_in.html")


@app.route("/launch_admin_portal", methods=["GET", "POST"])
def launch_admin_portal():
    intent = request.args.get("intent")
    portal_link = workos_client.portal.generate_link(organization=org_id, intent=intent)
    return redirect(portal_link["link"])
