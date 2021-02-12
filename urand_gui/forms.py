
from wtforms.fields import SubmitField, SelectField

from sqlalchemy import Table, Column, String, Enum
from wtforms_alchemy import ClassMap
from flask_wtf import Form

from urand import db
from collections import OrderedDict

from urand_gui import study, ModelForm


class FrmRandomizeParticipant(ModelForm):
	submit = SubmitField()
	cancel = SubmitField()
	class Meta:
		model = study.participant
		only = [c.name for c in study.participant.__table__.columns if (c.name in ['id', 'user']) or c.name.startswith('f_')]
		include_primary_keys = True

	def __init__(self, *args, **kwargs):
		super(FrmRandomizeParticipant, self).__init__(*args, **kwargs)

		self._fields = OrderedDict([(field, self._fields[field])
		                            for field in self._fields if field in study.participant.__table__.columns] +
		                           [(field, self._fields[field]) for field in ['submit', 'cancel']])




