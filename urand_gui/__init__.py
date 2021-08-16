import os

from wtforms_alchemy import model_form_factory
from flask_wtf import FlaskForm
from flask import Flask
from urand.config import config
from urand.study import Study


app = Flask(__name__)
app.secret_key = 'dev'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'

BaseModelForm = model_form_factory(FlaskForm)
# study = Study("Example Study")
study = Study("CHS JCOIN")


class ModelForm(BaseModelForm):
	@classmethod
	def get_session(self):
		return study.session
