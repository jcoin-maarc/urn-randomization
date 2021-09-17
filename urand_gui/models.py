from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_method
from .config import Config

db = SQLAlchemy()

user_to_study = db.Table('user_to_study',
                         db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                         db.Column('study_id', db.Integer, db.ForeignKey('study.id'), primary_key=True)
                         )


class Study(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(256), unique=True)


class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(128), unique=True, nullable=False)
	# Use for Oauth 2 authentication via Google
	email = db.Column(db.String(256), unique=True)
	# Generate with something like secrets.token_hex(32)
	api_key = db.Column(db.String(256))
	studies = db.relationship(Study, secondary=user_to_study, lazy='subquery',
	                       backref=db.backref('users', lazy=True))


class OAuth(OAuthConsumerMixin, db.Model):
	provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
	user = db.relationship(User)


# setup login manager
login_manager = LoginManager()
login_manager.login_view = 'google.login'


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))
