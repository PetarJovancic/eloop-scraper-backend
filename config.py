import os


class Config(object):
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URI')
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:dbpass@localhost/dbtest"
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')