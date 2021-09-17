import os
import base64

class Config(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    BOOTSTRAP_BTN_STYLE = 'primary'
    BOOTSTRAP_BTN_SIZE = 'sm'
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev'

