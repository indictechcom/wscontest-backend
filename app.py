import json
from datetime import date

import mwoauth
from flask import Flask, jsonify, redirect, request
from flask import session as flask_session
from flask import url_for
from flask_cors import CORS

from config import config
from models import Contest, ContestAdmin, ContestBook, Session

app = Flask(__name__)
app.secret_key = "b'C\x01\xe3j\xdcq\xe9\xa3&\x0b\x91\x82'"
CORS(app, resources={r"/*": {"origins": "*"}})


consumer_token = mwoauth.ConsumerToken(
    config["CONSUMER_KEY"], config["CONSUMER_SECRET"]
)

handshaker = mwoauth.Handshaker(config["OAUTH_MWURI"], consumer_token)


def _str(val):
    """
    Ensures that the val is the default str() type for python2 or 3
    """
    if str == bytes:
        if isinstance(val, str):
            return val
        else:
            return str(val)
    else:
        if isinstance(val, str):
            return val
        else:
            return str(val, "ascii")


@app.route("/login")
def login():

    redirect_to, request_token = handshaker.initiate()
    keyed_token_name = _str(request_token.key) + "_request_token"
    keyed_next_name = _str(request_token.key) + "_next"
    flask_session[keyed_token_name] = dict(zip(request_token._fields, request_token))

    if "next" in request.args:
        flask_session[keyed_next_name] = request.args.get("next")
    else:
        flask_session[keyed_next_name] = "index"

    return redirect(redirect_to)


@app.route("/logout")
def logout():
    flask_session["mwoauth_access_token"] = None
    flask_session["mwoauth_username"] = None
    if "next" in request.args:
        return redirect(request.args["next"])
    return jsonify("logged out !!")


@app.route("/oauth-callback")
def oauth_callback():
    request_token_key = request.args.get("oauth_token", "None")
    keyed_token_name = _str(request_token_key) + "_request_token"
    keyed_next_name = _str(request_token_key) + "_next"

    if keyed_token_name not in flask_session:
        err_msg = "OAuth callback failed. Can't find keyed token. Are cookies disabled?"
        return jsonify(f"error {err_msg}")

    access_token = handshaker.complete(
        mwoauth.RequestToken(**flask_session[keyed_token_name]), request.query_string
    )
    flask_session["mwoauth_access_token"] = dict(
        zip(access_token._fields, access_token)
    )

    next_url = url_for(flask_session[keyed_next_name])
    del flask_session[keyed_next_name]
    del flask_session[keyed_token_name]

    get_current_user(False)

    return redirect(next_url)


@app.before_request
def force_https():
    if request.headers.get("X-Forwarded-Proto") == "http":
        return redirect(
            "https://" + request.headers["Host"] + request.headers["X-Original-URI"],
            code=301,
        )


def get_current_user(cached=True):
    if cached:
        return flask_session.get("mwoauth_username")

    # Get user info
    identity = handshaker.identify(
        mwoauth.AccessToken(**flask_session["mwoauth_access_token"])
    )

    # Store user info in flask_session
    flask_session["mwoauth_username"] = identity["username"]
    flask_session["mwoauth_useremail"] = identity["email"]

    return flask_session["mwoauth_username"]


# route for the contest list view
@app.route("/contest-list", methods=["GET"])
def index():
    return jsonify("contest-list-here")


# route for graph data for specific contest
@app.route("/graph-data", methods=["GET"])
def graph_data():
    return jsonify("graph data here")


# route for contest info
@app.route("/contest-info")
def contest_info():
    return jsonify("contest-info-here")


@app.route("/contest/create", methods=["GET", "POST"])
def create_contest():
    if request.method == "GET":
        return json.dumps({})

    elif request.method == "POST" and get_current_user() is not None:
        try:
            req = request.form
            session = Session()

            contest = Contest(
                name=req["c_name"],
                created_by=get_current_user(),
                start_date=date.fromisoformat(req["start_date"]),
                end_date=date.fromisoformat(req["end_date"]),
                status=True,
                point_per_proofread=int(req["p_proofread"]),
                point_per_validate=int(req["p_validate"]),
                lang=req["language"],
            )
            session.add(contest)

            book_names = req.get("book_name").split("\r\n")
            for book in book_names:
                session.add(ContestBook(name=book.split(":")[1], contest=contest))

            admins = req.get("c_admin").split("\r\n")
            for admin_name in admins:
                admin = (
                    session.query(ContestAdmin).filter_by(user_name=admin_name).first()
                )
                # If admin is already in database, just add a new contest to his list
                if admin:
                    admin.contests.append(contest)
                else:
                    session.add(ContestAdmin(user_name=admin_name, contests=[contest]))

            session.commit()

            return (
                json.dumps({"success": True}),
                200,
                {"ContentType": "application/json"},
            )
        except Exception as e:
            return (
                json.dumps({"success": False, "message": str(e)}),
                404,
                {"ContentType": "application/json"},
            )


if __name__ == "__main__":
    app.run(debug=True)

