from flask import Flask, jsonify, CORS

app = Flask(__name__)
app.secret_key = "b'C\x01\xe3j\xdcq\xe9\xa3&\x0b\x91\x82'"

CORS(app, resources={r"/*": {"origins": "*"}})


# route for the contest list view
@app.route("/contest-list", methods=["GET"])
def index():
    return jsonify("contest-list-here")

#route for graph data for specific contest
@app.route("/graph-data", methods=['GET'])
def graph-data():
    return jsonify("graph data here")   

#route for contest info
@app.route("/contest-info")
def contest_info(): 
    return jsonify("contest-info-here")


@app.route("")
if __name__ == "__main__":
    app.run()
