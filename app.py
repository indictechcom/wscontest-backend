from datetime import date
from typing import Dict, Optional, Tuple, Union

from authlib.integrations.flask_client import OAuth
from flask import Flask, Response, jsonify, redirect, request
from flask import session as flask_session
from flask_cors import CORS
from flask_migrate import Migrate
from config import config
from models import Book, Contest, ContestAdmin, IndexPage, Session, User, engine

app = Flask(__name__)
app.secret_key = config["APP_SECRET_KEY"]

CORS(app, origins="*", supports_credentials=True)


oauth = OAuth(app)
oauth.register(
    name=config["APP_NAME"],
    client_id=config["CONSUMER_KEY"],
    client_secret=config["CONSUMER_SECRET"],
    access_token_url="https://commons.wikimedia.org/w/rest.php/oauth2/access_token",
    authorize_url="https://commons.wikimedia.org/w/rest.php/oauth2/authorize",
    api_base_url="https://commons.wikimedia.org/w",
    client_kwargs={},
)

migrate = Migrate(app, db)

ws_contest = oauth.create_client("ws test 5")


def _str(val: Union[str, bytes]) -> str:
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

@app.route("/api/login")
def login() -> Response:
    return ws_contest.authorize_redirect() 
    

@app.route("/api/logout")
def logout() -> Union[Response, Tuple[Response, int]]:
    flask_session.clear()
    if "next" in request.args:
        return redirect(request.args["next"])
    return jsonify({"status": "logged out"})


@app.route("/oauth-k")
def authorize() -> Response:
    token = ws_contest.authorize_access_token()
    if token:
        resp = ws_contest.get("/w/rest.php/oauth2/resource/profile", token=token)
        resp.raise_for_status()
        profile = resp.json()
        print(profile)
        flask_session['profile'] = profile
    return redirect("http://localhost:5173/contest")


@app.before_request
def force_https() -> Optional[Response]:
    if request.headers.get("X-Forwarded-Proto") == "http":
        return redirect(
            "https://" + request.headers["Host"] + request.headers["X-Original-URI"],
            code=301,
        )
    return None


def get_current_user(cached: bool = True) -> Optional[str]:
    if cached:
        print(flask_session)


@app.route("/api/graph-data", methods=["GET"])
def graph_data() -> Response:
    return jsonify("graph data here")


@app.route("/api/contest/create", methods=["POST"])
def create_contest() -> Tuple[Response, int]:
    get_current_user(True)


@app.route("/contest/create", methods=["POST"])
def create_contest() -> Tuple[Response, int]:
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
                if admin:
                    admin.contests.append(contest)
                else:
                    session.add(ContestAdmin(user_name=admin_name, contests=[contest]))

            session.commit()

            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 404


@app.route("/api/contests", methods=["GET"])
def contest_list() -> Tuple[Response, int]:
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


@app.route("/api/contest/<int:id>")
def contest_by_id(id: int) -> Tuple[Response, int]:
    session = Session()
    contest = session.get(Contest, id)
    if not contest:
        return jsonify("Contest with this id does not exist!"), 404
    else:
        data: Dict = {}
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

