from server import db

class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.Integer, primary_key = True)
    ig_id = db.Column(db.String(50))    
    username = db.Column(db.String(50))    
    full_name = db.Column(db.String(50))
    posts = db.Column(db.Integer)
    followers = db.Column(db.Integer)
    following = db.Column(db.Integer)
    profile_pic = db.Column(db.VARCHAR(2048))