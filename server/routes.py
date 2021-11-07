from server.controller import post_data
from server import app
from flask import request


@app.route('/profile', methods=['POST'])
def post_profile():
    data = request.get_json()
    username = data['body']["username"]
    password = data['body']["password"]
    profile = data['body']["profile"]
    result = post_data(username, password, profile)
    
    return result
