from server.controller import post_data
from server import app
import os


@app.route('/profile', methods=['POST'])
def post_profile():
    username = os.environ.get('IG_USER')
    password = os.environ.get('IG_PASSWORD')
    profile = os.environ.get('IG_PROFILE')
    result = post_data(username,password, profile)

    return result