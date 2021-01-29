# -*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, render_template, request, flash, Markup, jsonify
from flask_wtf import Form, FlaskForm, CSRFProtect

from wtforms import StringField, SubmitField, BooleanField, PasswordField, IntegerField, TextField,\
    FormField, SelectField, FieldList

from wtforms.validators import DataRequired, Length
from wtforms.fields import *


from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy, BaseQuery

from urand.study import Study
from urand import db
import pandas as pd
import app.forms as urand_forms

study = Study("Example Study")
app = Flask(__name__)
app.secret_key = 'dev'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'
# app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'lumen'  # uncomment this line to test bootswatch theme

bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
csrf = CSRFProtect(app)


@app.before_first_request
def before_first_request_func():
    db.drop_all()
    db.create_all()
    db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_participant', methods=['GET', 'POST'])
def frm_add_participant():
    form = urand_forms.Participant()
    if form.validate_on_submit():
        participant = study.participant()
        form.populate_obj(participant)
        pdf_participants = pd.DataFrame([participant.__dict__], index=[0])
        pdf_participants = pdf_participants[[col for col in pdf_participants.columns if col in [c.name for c in study.participant.__table__.columns]]]
        print(pdf_participants)
        study.upload_new_participants(pdf=pdf_participants)
        return redirect(url_for('list_participants'))
    return render_template('frm_add_participant.html', participant_form=form)


@app.route('/list_participants', methods=['GET', 'POST'])
def list_participants():
    query = BaseQuery([study.participant], study.session)
    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page, per_page=10)
    participants = pagination.items
    titles = [('id', '#'), ('f_institute', 'Institute'), ('f_pretreatment', 'Pretreatment'),
              ('f_sex', 'Sex'), ('trt', 'Treatment'), ('datetime', 'Date Assigned'), ('user', 'User')]
    return render_template('list_participants.html', title='Participants',
                           pagination=pagination, entities=participants, titles=titles)


if __name__ == '__main__':
    app.run(debug=True)
