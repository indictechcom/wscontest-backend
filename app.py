from datetime import date

import mwoauth
from flask import Flask, jsonify, redirect, request
from flask import session as flask_session
from flask import url_for
from flask_cors import CORS

from config import config
from models import Book, Contest, ContestAdmin, IndexPage, Session, User

app = Flask(__name__)
app.secret_key = "b'C\x01\xe3j\xdcq\xe9\xa3&\x0b\x91\x82'"
CORS(app, origins="*", supports_credentials=True)


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
    flask_session.clear()
    if "next" in request.args:
        return redirect(request.args["next"])
    return jsonify({"status": "logged out"})



@app.route("/oauth-callback")
def oauth_callback():
    request_token_key = request.args.get("oauth_token", "None")
    keyed_token_name = _str(request_token_key) + "_request_token"

    if keyed_token_name not in flask_session:
        err_msg = "OAuth callback failed. Can't find keyed token. Are cookies disabled?"
        return jsonify(f"error {err_msg}")

    access_token = handshaker.complete(
        mwoauth.RequestToken(**flask_session[keyed_token_name]), request.query_string
    )
    flask_session["mwoauth_access_token"] = dict(
        zip(access_token._fields, access_token)
    )
    flask_session.modified = True  # Ensure the session is marked as modified
    print(access_token)

    # Clean up the temporary request token
    del flask_session[keyed_token_name]

    # Load the current user to populate session data
    get_current_user(False)
    return redirect("http://localhost:5173/Contest")


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
    print(flask_session["mwoauth_username"])
    return flask_session["mwoauth_username"]


# route for graph data for specific contest
@app.route("/graph-data", methods=["GET"])
def graph_data():
    return jsonify("graph data here")


@app.route("/contest/create", methods=["POST"])
def create_contest():
    if get_current_user(False) is None:
        return (
            jsonify("Please login!"),
            403,
        )

    if request.method == "POST":
        try:
            data = request.json
            session = Session()

            contest = Contest(
                name=data["name"],
                created_by=get_current_user(),
                start_date=date.fromisoformat(data["start_date"]),
                end_date=date.fromisoformat(data["end_date"]),
                status=True,
                point_per_proofread=int(data["proofread_points"]),
                point_per_validate=int(data["validate_points"]),
                lang=data["language"],
            )
            session.add(contest)

            book_names = data.get("book_names").split("\n")
            for book in book_names:
                session.add(Book(name=book.split(":")[1], contest=contest))

            admins = data.get("admins").split("\n")
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

            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 404


@app.route("/contests", methods=["GET"])
def contest_list():
    session = Session()
    contests = (
        session.query(Contest)
        .with_entities(
            Contest.name, Contest.start_date, Contest.end_date, Contest.status
        )
        .all()
    )

    return (
        jsonify(
            [
                {
                    "name": name,
                    "start_date": start_date.strftime("%d-%m-%Y"),
                    "end_date": end_date.strftime("%d-%m-%Y"),
                    "status": status,
                }
                for name, start_date, end_date, status in contests
            ]
        ),
        200,
    )


@app.route("/contest/<int:id>")
def contest_by_id(id):
    session = Session()
    contest = session.get(Contest, id)
    if not contest:
        return jsonify("Contest with this id does not exist!"), 404
    else:
        data = {}
        data["contest_details"] = contest
        data["adminstrators"] = [admin.user_name for admin in contest.admins]
        data["books"] = [book.name for book in contest.books]

        data["users"] = []
        for user in session.query(User).filter(User.cid == id).all():
            proofread_count = len(user.proofread_pages)
            validated_count = len(user.validated_pages)
            points = (proofread_count * contest.point_per_proofread) + (
                validated_count * contest.point_per_validate
            )
            data["users"].append(
                {
                    user.user_name: {
                        "proofread_count": proofread_count,
                        "validated_count": validated_count,
                        "points": points,
                        "pages": session.query(IndexPage)
                        # Finds pages which the user has contributed to
                        .filter(
                            (IndexPage.validator_username == user.user_name)
                            | (IndexPage.proofreader_username == user.user_name)
                        ).all(),
                    }
                }
            )
        return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=True)

