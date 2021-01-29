from wtforms_alchemy import model_form_factory
from wtforms.fields import SubmitField
from flask_wtf import FlaskForm
from sqlalchemy import Table, Column, String, Enum
from wtforms_alchemy import ClassMap
from urand.study import Study
from urand import db
from collections import OrderedDict

study = Study("Example Study")
BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
	@classmethod
	def get_session(self):
		return study.session


class Participant(ModelForm):
	submit = SubmitField()
	cancel = SubmitField()
	class Meta:
		model = study.participant
		only = [c.name for c in study.participant.__table__.columns if (c.name in ['id', 'user']) or c.name.startswith('f_')]

	def __init__(self, *args, **kwargs):
		super(Participant, self).__init__(*args, **kwargs)

		self._fields = OrderedDict([(field, self._fields[field])
		                            for field in self._fields if field in study.participant.__table__.columns] +
		                           [(field, self._fields[field]) for field in ['submit', 'cancel']])



