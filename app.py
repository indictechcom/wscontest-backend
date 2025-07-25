from datetime import date
from typing import Dict, List, Optional, Tuple, Union, Any

from mwoauth import ConsumerToken, Handshaker, RequestToken
from flask import Flask, Response, jsonify, redirect, request
from flask import session as flask_session
from flask_cors import CORS
from extensions import db, migrate
from config import config
from models import Book, Contest, ContestAdmin, IndexPage, User

app: Flask = Flask(__name__)
app.secret_key = config["APP_SECRET_KEY"]

app.config['SQLALCHEMY_DATABASE_URI'] = config["SQL_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate.init_app(app, db)

consumer_token: ConsumerToken = ConsumerToken(
    config["CONSUMER_KEY"], config["CONSUMER_SECRET"]
)
WIKI_OAUTH_URL = "https://meta.wikimedia.org/w/index.php"

CORS(app, origins="[http://localhost:5173]", supports_credentials=True)

"""oAut logic"""


@app.route("/login")
def login() -> Response:
    handshaker = Handshaker(WIKI_OAUTH_URL, consumer_token)
    
    redirect_url, request_token = handshaker.initiate()
    
    flask_session['request_token_key'] = request_token.key
    flask_session['request_token_secret'] = request_token.secret
    
    flask_session['return_to_url'] = request.args.get('next', 'http://localhost:5173')
    
    return redirect(redirect_url)

@app.route("/logout")
def logout() -> Response:
    flask_session.clear()
    return redirect(request.args.get('next', '/'))

@app.route("/complete-login")
def complete_login() -> Response:
    handshaker = Handshaker(WIKI_OAUTH_URL, consumer_token)
    
    rt_key = flask_session.get('request_token_key')
    rt_secret = flask_session.get('request_token_secret')
    
    if not rt_key or not rt_secret:
        return redirect('/login')
    
    request_token = RequestToken(rt_key, rt_secret)
    
    try:
        access_token = handshaker.complete(request_token, request.query_string)
        identity = handshaker.identify(access_token)
        
        userid = identity['sub']
        username = identity['username']
        
        # Store user info in session
        flask_session['userid'] = userid
        flask_session['username'] = username
        
        print(f"Logged in user: {username} (ID: {userid})")
        
        # Always redirect to frontend after successful login
        return_url = flask_session.pop('return_to_url', 'http://localhost:5173')
        return redirect(return_url)
        
    except Exception as e:
        print(f"OAuth error: {e}")
        return redirect('/login')

""" Logical routes for the app """

def get_current_user(cached: bool = True) -> Optional[str]:
    return flask_session.get('username')

@app.route("/api/graph-data", methods=["GET"])
def graph_data() -> Response:
    return jsonify("graph data here")


@app.route("/api/contest/create", methods=["POST"])
def create_contest_api() -> Tuple[Response, int]:
    get_current_user(True)
    #! This function seems incomplete, needs implementation
    return jsonify({"error": "Not implemented"}), 501


@app.route("/contest/create", methods=["POST"])
def create_contest() -> Tuple[Response, int]:
    if get_current_user(False) is None:
        return (
            jsonify("Please login!"),
            403,
        )

    if request.method == "POST":
        try:
            data: Dict[str, Any] = request.json

            contest: Contest = Contest(
                name=data["name"],
                created_by=get_current_user(),
                start_date=date.fromisoformat(data["start_date"]),
                end_date=date.fromisoformat(data["end_date"]),
                status=True,
                point_per_proofread=int(data["proofread_points"]),
                point_per_validate=int(data["validate_points"]),
                lang=data["language"],
            )
            db.session.add(contest)

            book_names: List[str] = data.get("book_names").split("\n")
            for book in book_names:
                db.session.add(Book(name=book.split(":")[1], contest=contest))

            admins: List[str] = data.get("admins").split("\n")
            for admin_name in admins:
                admin: Optional[ContestAdmin] = ContestAdmin.query.filter_by(user_name=admin_name).first()
                if admin:
                    admin.contests.append(contest)
                else:
                    db.session.add(ContestAdmin(user_name=admin_name, contests=[contest]))

            db.session.commit()

            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 404


@app.route("/api/contests", methods=["GET"])
def contest_list() -> Tuple[Response, int]:
    contests: List[Tuple[str, date, date, bool]] = (
        Contest.query
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
    contest: Optional[Contest] = Contest.query.get(id)
    if not contest:
        return jsonify("Contest with this id does not exist!"), 404
    else:
        data: Dict[str, Any] = {}
        data["contest_details"] = contest
        data["adminstrators"] = [admin.user_name for admin in contest.admins]
        data["books"] = [book.name for book in contest.books]

        data["users"] = []
        for user in User.query.filter(User.cid == id).all():
            proofread_count: int = len(user.proofread_pages)
            validated_count: int = len(user.validated_pages)
            points: int = (proofread_count * contest.point_per_proofread) + (
                validated_count * contest.point_per_validate
            )
            data["users"].append(
                {
                    user.user_name: {
                        "proofread_count": proofread_count,
                        "validated_count": validated_count,
                        "points": points,
                        "pages": IndexPage.query
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

