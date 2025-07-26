from datetime import date, datetime
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

CORS(app, origins=["http://localhost:5173"], supports_credentials=True)


"""oAuth logic"""

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

@app.route("/user", methods=["GET"])
def get_user_info() -> Tuple[Response, int]:
    username = get_current_user()
    if username:
        return jsonify({
            "logged_in": True,
            "username": username,
            "userid": flask_session.get('userid')
        }), 200
    else:
        return jsonify({
            "logged_in": False,
            "username": None,
            "userid": None
        }), 200

@app.route("/graph-data", methods=["GET"])
def graph_data() -> Response:
    return jsonify("graph data here")


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
                book_name = book.split(":")[1]
                existing_book: Optional[Book] = Book.query.filter_by(name=book_name).first()
                if existing_book:
                    # Book already exists, add this contest to it if not already added
                    if contest not in existing_book.contests:
                        existing_book.contests.append(contest)
                else:
                    # Create new book and add the contest to it
                    new_book = Book(name=book_name)
                    new_book.contests.append(contest)
                    db.session.add(new_book)

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
            print(f"Error creating contest: {e}")
            return jsonify({"success": False, "message": str(e)}), 404


@app.route("/contests", methods=["GET"])
def contest_list() -> Tuple[Response, int]:
    contests: List[Contest] = Contest.query.all()
    
    result = []
    for contest in contests:
        current_date = datetime.now().date()
        contest_end_date = contest.end_date.date() if hasattr(contest.end_date, 'date') else contest.end_date
        is_running = current_date <= contest_end_date and contest.status is not False
        
        result.append({
            "id": contest.cid,  
            "name": contest.name,
            "start_date": contest.start_date.strftime("%d-%m-%Y"),
            "end_date": contest.end_date.strftime("%d-%m-%Y"),
            "status": is_running,  
        })
    
    return jsonify(result), 200


@app.route("/contest/<int:id>")
def contest_by_id(id: int) -> Tuple[Response, int]:
    contest: Optional[Contest] = Contest.query.get(id)
    if not contest:
        return jsonify("Contest with this id does not exist!"), 404
    else:
        data: Dict[str, Any] = {}

        data["contest_details"] = {
            "cid": contest.cid,
            "name": contest.name,
            "created_by": contest.created_by,
            "createdon": contest.createdon.isoformat() if contest.createdon else None,
            "start_date": contest.start_date.isoformat() if contest.start_date else None,
            "end_date": contest.end_date.isoformat() if contest.end_date else None,
            "status": contest.status,
            "point_per_proofread": contest.point_per_proofread,
            "point_per_validate": contest.point_per_validate,
            "lang": contest.lang
        }
        data["adminstrators"] = [admin.user_name for admin in contest.admins]
        data["books"] = [book.name for book in contest.books]

        data["users"] = []
        for user in contest.users:
            proofread_count: int = len(user.proofread_pages)
            validated_count: int = len(user.validated_pages)
            points: int = (proofread_count * contest.point_per_proofread) + (
                validated_count * contest.point_per_validate
            )
            
            user_pages = []
            contest_book_names = [book.name for book in contest.books]
            for page in IndexPage.query.filter(
                (IndexPage.validator_username == user.user_name) |
                (IndexPage.proofreader_username == user.user_name)
            ).all():
                if page.book_name in contest_book_names:
                    user_pages.append({
                        "id": page.id,
                        "page_name": page.page_name,
                        "book_name": page.book_name,
                        "validate_time": page.validate_time.isoformat() if page.validate_time else None,
                        "proofread_time": page.proofread_time.isoformat() if page.proofread_time else None,
                        "v_revision_id": page.v_revision_id,
                        "p_revision_id": page.p_revision_id
                    })
            
            data["users"].append({
                user.user_name: {
                    "proofread_count": proofread_count,
                    "validated_count": validated_count,
                    "points": points,
                    "pages": user_pages,
                }
            })
        return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=True)

