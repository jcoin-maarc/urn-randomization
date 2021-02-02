# -*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, render_template, request,  jsonify, render_template, request
from flask_wtf import CSRFProtect

from datatables import ColumnDT, DataTables

from sqlalchemy.orm import load_only

from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy, BaseQuery

import app.utils as utils
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
def add_participant():
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


@app.route("/participants")
def list_participants():
    """List users with DataTables <= 1.10.x."""
    for c in study.participant.__table__.columns:
        print(c.info)
    return render_template("tbl_participant.html", project="participants",
                           colnames=[c.info.get('label', c.name) for c in study.participant.__table__.columns
                                     if (c.name not in ['bg_state'])])


# @app.route("/dt_110x")
# def dt_110x():
#     """List users with DataTables <= 1.10.x."""
#     colnames=[c.name for c in User.__table__.columns
#                                      ]
#     return render_template("dt_110x.html", project="dt_110x", colnames=colnames)


@app.route("/data")
def data():
    """Return server side data."""
    # defining columns
    # columns = [
    #     ColumnDT(User.id),
    #     ColumnDT(User.name),
    #     ColumnDT(User.created_at),
    # ]
    lst_col_to_load = [c.name for c in study.participant.__table__.columns if (c.name not in ['id', 'bg_state'])]
    columns = [ColumnDT(study.participant.__dict__['id'], column_name='id')] +\
              [ColumnDT(study.participant.__dict__[col], column_name=col) for col in lst_col_to_load]

    # defining the initial query depending on your purpose
    query = study.session.query(study.participant)
    # query = db.session.query().select_from(User)
    # GET parameters
    params = request.args.to_dict()

    # instantiating a DataTable for the query and table needed
    row_table = DataTables(params, query, columns)

    # returns what is needed by DataTable
    dct_result = row_table.output_result()
    for item in dct_result['data']:
        item['0'] = item['0'].id
    return jsonify(dct_result)
    # return jsonify(rowTable.output_result())

# @app.route("/dt_110x")
# def dt_110x():
#     """List users with DataTables <= 1.10.x."""
#     return render_template("dt_110x.html", project="dt_110x",
#                            colnames=[c.name for c in study.participant.__table__.columns
#                                      if (c.name not in ['bg_state'])])
# # def list_participants():
# #     query = BaseQuery([study.participant], study.session)
# #     page = request.args.get('page', 1, type=int)
# #     pagination = query.paginate(page, per_page=10)
# #     participants = pagination.items
# #     titles = [('id', '#'), ('f_institute', 'Institute'), ('f_pretreatment', 'Pretreatment'),
# #               ('f_sex', 'Sex'), ('trt', 'Treatment'), ('datetime', 'Date Assigned'), ('user', 'User')]
# #     return render_template('tbl_participant.html', title='Participants',
# #                            pagination=pagination, entities=participants, titles=titles)
#
#
# @app.route('/data')
# def data():
#     """Return server side data."""
#     # defining columns
#
#     participant = study.participant
#     participant.serialized = property(lambda self: {'id': self.id})
#     participant.__unicode__ = utils.__unicode__
#     participant.__repr__ = utils.__repr__
#
#     lst_col_to_load = [c.name for c in study.participant.__table__.columns if (c.name not in ['id', 'bg_state'])]
#     columns = [ColumnDT(study.participant.__dict__['id'], column_name='id')] +\
#               [ColumnDT(study.participant.__dict__[col], column_name=col) for col in lst_col_to_load]
#
#     # defining the initial query depending on your purpose
#     query = study.session.query(study.participant)
#     print(query)
#     # GET parameters
#     params = request.args.to_dict()
#     # params['length'] = 30
#     # params['start'] = 0
#     # instantiating a DataTable for the query and table needed
#     row_table = DataTables(params, query, columns)
#
#     # returns what is needed by DataTable
#     dct_result = row_table.output_result()
#     print(dct_result)
#     for item in dct_result['data']:
#         print(item)
#         item['0'] = item['0'].id
#
#     print(dct_result)
#     return jsonify(dct_result)


if __name__ == '__main__':
    app.run(debug=True)
