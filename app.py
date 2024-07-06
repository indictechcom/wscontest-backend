from flask import Flask, jsonify, session as flask_session, redirect, request, url_for, abort
from flask_cors import CORS
from models import Contest, ContestAdmin, ContestBook, IndexPage, UnlistedUser, Session
from config import config

app = Flask(__name__)
app.secret_key = "b'C\x01\xe3j\xdcq\xe9\xa3&\x0b\x91\x82'"

CORS(app, resources={r"/*": {"origins": "*"}})

import mwoauth
from datetime import datetime
from pytz import timezone 

consumer_token = mwoauth.ConsumerToken(
    config["CONSUMER_KEY"],
    config["CONSUMER_SECRET"]
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
            return str(val, 'ascii')

@app.route('/login')
def login():
    
    redirect_to, request_token = handshaker.initiate()
    keyed_token_name = _str(request_token.key) + '_request_token'
    keyed_next_name = _str(request_token.key) + '_next'
    flask_session[keyed_token_name] = \
        dict(zip(request_token._fields, request_token))

    if 'next' in request.args:
        flask_session[keyed_next_name] = request.args.get('next')
    else:
        flask_session[keyed_next_name] = 'index'

    return redirect(redirect_to)

@app.route('/logout')
def logout():
    flask_session['mwoauth_access_token'] = None
    flask_session['mwoauth_username'] = None
    if 'next' in request.args:
        return redirect(request.args['next'])
    return jsonify("logged out !!")
    

@app.route('/oauth-callback')
def oauth_callback():
    request_token_key = request.args.get('oauth_token', 'None')
    keyed_token_name = _str(request_token_key) + '_request_token'
    keyed_next_name = _str(request_token_key) + '_next'

    if keyed_token_name not in flask_session:
        err_msg = "OAuth callback failed. Can't find keyed token. Are cookies disabled?"
        return jsonify(f"error {err_msg}")

    access_token = handshaker.complete(
        mwoauth.RequestToken(**flask_session[keyed_token_name]),
        request.query_string)   
    flask_session['mwoauth_access_token'] = \
        dict(zip(access_token._fields, access_token))

    next_url = url_for(flask_session[keyed_next_name])
    del flask_session[keyed_next_name]
    del flask_session[keyed_token_name]

    get_current_user(False)

    return redirect(next_url)

@app.before_request
def force_https():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        return redirect(
            'https://' + request.headers['Host'] + request.headers['X-Original-URI'],
            code=301
        )


def get_current_user(cached=True):
    if cached:
        return flask_session.get('mwoauth_username')

    # Get user info
    identity = handshaker.identify(
        mwoauth.AccessToken(**flask_session['mwoauth_access_token']))

    # Store user info in flask_session
    flask_session['mwoauth_username'] = identity['username']
    flask_session['mwoauth_useremail'] = identity['email']

    return flask_session['mwoauth_username']

# route for the contest list view
@app.route("/contest-list", methods=["GET"])
def index():
    return jsonify("contest-list-here")

#route for graph data for specific contest
@app.route("/graph-data", methods=['GET'])
def graph_data():
    return jsonify("graph data here")   

#route for contest info
@app.route("/contest-info")
def contest_info(): 
    return jsonify("contest-info-here")

if __name__ == "__main__":
    app.run(debug=True)
