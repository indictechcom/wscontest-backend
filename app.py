from flask import Flask, jsonify

app = Flask(__name__)

CORS(app, resources={r'/*': {'origins': '*'}})

#route for the contest list view
@app.route("/contest-list", methods=['GET'])
def index():
    return jsonify("contest-list-here")

#route for graph data for specific contest
@app.route("/graph-data", methods=['GET'])
def graph-data:
    return jsonify("graph data here")



if __name__ == "__main__":
    app.run()

    
