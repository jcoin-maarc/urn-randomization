
from wtforms.fields import SubmitField, StringField

from sqlalchemy import Table, Column, String, Enum
from wtforms_alchemy import ClassMap
from flask_wtf import Form
from wtforms.validators import Optional

from urand import db
from collections import OrderedDict

from urand_gui import study, ModelForm

from wtforms.validators import Optional, InputRequired


class OptionalIfDisabled(Optional):
	def __call__(self, form, field):
		if field.render_kw is not None and field.render_kw.get('disabled', False):
			field.flags.disabled = True
			super(OptionalIfDisabled, self).__call__(form, field)


class FrmRandomizeParticipant(ModelForm):
	submit = SubmitField()
	cancel = SubmitField()
	user = StringField(label='Added by',
	                   validators=[OptionalIfDisabled(), InputRequired()])

	class Meta:
		model = study.participant
		only = [c.name for c in study.participant.__table__.columns if (c.name in ['id']
		                                                                ) or c.name.startswith('f_')]
		include_primary_keys = True

	def __init__(self, *args, **kwargs):
		super(FrmRandomizeParticipant, self).__init__(*args, **kwargs)
		self._fields = OrderedDict([(field, self._fields[field])
		                            for field in self._fields if (field in study.participant.__table__.columns) and
		                            (field != 'user')] +
		                           [(field, self._fields[field]) for field in ['user', 'submit', 'cancel']])

		self.user.render_kw = {'disabled': True}




