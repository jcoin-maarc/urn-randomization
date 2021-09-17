import os

from wtforms_alchemy import model_form_factory
from flask_wtf import FlaskForm
from flask import Flask, request, redirect, jsonify, url_for
from flask_bootstrap import Bootstrap
from urand.config import config as urand_config
from urand.study import Study
from .config import Config as FlaskConfig
from .oauth import blueprint
from .models import db, login_manager, User
from .cli import create_db, add_user, list_users, delete_user

study = Study("CHS JCOIN")

app = Flask(__name__)
app.config.from_object(FlaskConfig)
app.register_blueprint(blueprint, url_prefix='/login')
app.cli.add_command(create_db)
app.cli.add_command(add_user)
app.cli.add_command(list_users)
app.cli.add_command(delete_user)
app.config['SQLALCHEMY_DATABASE_URI'] = urand_config['db'].get()
db.init_app(app)
login_manager.init_app(app)
bootstrap = Bootstrap(app)


@login_manager.request_loader
def load_user(request):
	"""Attempt to authenticate user using API key"""

	api_key = request.form.get('api_key')
	if api_key:
		user = User.query.filter_by(api_key=api_key).first()
		if user:
			return user

	return None


@login_manager.unauthorized_handler
def unauthorized():
	"""Respond to unauthorized requests"""

	if request.form.get('api_key'):
		return jsonify({"message": "Unauthorized request"}), 401

	return redirect(url_for('index'))


BaseModelForm = model_form_factory(FlaskForm)
# study = Study("Example Study")


class ModelForm(BaseModelForm):
	@classmethod
	def get_session(self):
		return study.session
