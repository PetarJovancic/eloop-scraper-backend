from igramscraper.instagram import Instagram
from time import sleep
from flask import jsonify
from server import db
from server.models import Profile


def fetch_data(username, password, profile):  
    instagram = Instagram()
    instagram.with_credentials(username, password)
    instagram.login()

    sleep(2)

    account = instagram.get_account(profile)
    dicts = account.__dict__

    return dicts

def post_data(username, password, profile):
    data = fetch_data(username, password, profile)
    
    duplicate = db.session.query(Profile).filter(
        Profile.username == profile).first()

    if not duplicate:
        new_profile = Profile(
                        ig_id = data["identifier"],
                        username=data['username'],
                        full_name=data['full_name'],
                        posts=data['media_count'],
                        followers=data['followed_by_count'],
                        following=data['follows_count'],
                        profile_pic=data['profile_pic_url_hd'])

        db.session.add(new_profile)
        db.session.commit()

    return data
