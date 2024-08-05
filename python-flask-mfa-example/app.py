import os
from typing import Any, cast
from flask import Flask, session, redirect, render_template, request, url_for, jsonify
import json
import workos
from flask_lucide import Lucide

# Flask Setup
DEBUG = False
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")
lucide = Lucide(app)

# WorkOS Setup

workos.api_key = os.getenv("WORKOS_API_KEY")
workos.client_id = os.getenv("WORKOS_CLIENT_ID")
workos.base_api_url = "http://localhost:7000/" if DEBUG else workos.base_api_url


@app.route("/")
def home():
    if session.get("factor_list") == None:
        session["factor_list"] = []
        session["current_factor_qr"] = ""
        session["phone_number"] = ""

    if session["factor_list"] != None:
        return render_template("list_factors.html", factors=session["factor_list"])

    return render_template(
        "list_factors.html",
    )


@app.route("/enroll_factor_details", methods=["GET"])
def enroll_factor_details():
    return render_template("enroll_factor.html")


@app.route("/enroll_sms_factor", methods=["POST"])
def enroll_sms_factor():
    factor_type = request.form.get("type")
    phone_number = request.form.get("phone_number")
    if not factor_type in ("sms", "totp"):
        return "Invalid factor type"

    new_factor = workos.client.mfa.enroll_factor(
        type=factor_type, phone_number=phone_number
    )

    session["factor_list"].append(new_factor.dict())
    session.modified = True
    return redirect("/")


@app.route("/enroll_totp_factor", methods=["POST"])
def enroll_totp_factor():
    data = cast(Any, request.get_json())
    type = data["type"]
    issuer = data["issuer"]
    user = data["user"]

    new_factor = workos.client.mfa.enroll_factor(
        type=type, totp_issuer=issuer, totp_user=user
    )

    if new_factor.type == "totp":
        session["current_factor_qr"] = new_factor.totp.qr_code
    session["factor_list"].append(new_factor.dict())
    session.modified = True
    return jsonify(new_factor.dict())


@app.route("/factor_detail")
def factor_detail():
    factorId = request.args.get("id")
    for factor in session["factor_list"]:
        if factor["id"] == factorId:
            fullFactor = factor

        phone_number = "-"
        if factor["type"] == "sms":
            phone_number = factor["sms"]["phone_number"]

    session["current_factor"] = fullFactor["id"]
    session["current_factor_type"] = fullFactor["type"]
    session.modified = True
    return render_template(
        "factor_detail.html",
        factor=fullFactor,
        phone_number=phone_number,
    )


@app.route("/challenge_factor", methods=["POST"])
def challenge_factor():
    if session["current_factor_type"] == "sms":
        message = request.form["sms_message"]
        session["sms_message"] = message

        challenge = workos.client.mfa.challenge_factor(
            authentication_factor_id=session["current_factor"],
            sms_template=message,
        )

    if session["current_factor_type"] == "totp":
        authentication_factor_id = session["current_factor"]
        challenge = workos.client.mfa.challenge_factor(
            authentication_factor_id=authentication_factor_id,
        )

    session["challenge_id"] = challenge.id
    session.modified = True
    return render_template("challenge_factor.html")


@app.route("/verify_factor", methods=["POST"])
def verify_factor():
    def buildCode(code_values):
        code = ""
        for x in code_values.values():
            code += x
        return code

    code = buildCode(request.form)
    challenge_id = session["challenge_id"]
    verify_factor = workos.client.mfa.verify_challenge(
        authentication_challenge_id=challenge_id,
        code=code,
    )

    return render_template(
        "challenge_success.html",
        challenge=verify_factor.challenge,
        valid=verify_factor.valid,
        type=session["current_factor_type"],
    )


@app.route("/clear_session", methods=["GET"])
def clear_session():
    session.clear()
    return redirect("/")
