from flask import Flask, jsonify

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


if __name__ == "__main__":
    app.run()
