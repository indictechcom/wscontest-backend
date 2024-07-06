import json
from datetime import date

from flask import Flask, jsonify, request
from flask_cors import CORS

from models import Contest, ContestAdmin, ContestBook, Session

app = Flask(__name__)
app.secret_key = "b'C\x01\xe3j\xdcq\xe9\xa3&\x0b\x91\x82'"
CORS(app, resources={r"/*": {"origins": "*"}})


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

    # TODO: Replace with User AUTH
    elif request.method == "POST" and True:
        try:
            req = request.form
            session = Session()

            contest = Contest(
                name=req["c_name"],
                created_by="TEMP",
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
