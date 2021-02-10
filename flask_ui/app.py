# -*- coding: utf-8 -*-
from flask import redirect, url_for, render_template, request,  jsonify, render_template, request
from flask_wtf import CSRFProtect


from datatables import ColumnDT, DataTables

from flask_bootstrap import Bootstrap

import pandas as pd
import flask_ui.forms as urand_forms
import flask_ui.plots as plot_utils

from flask_ui import study, app, Study, config


# app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'lumen'  # uncomment this line to test bootswatch theme

bootstrap = Bootstrap(app)
csrf = CSRFProtect(app)

lst_col_to_defer = ['bg_state']
lst_numeric_col = ['id']
lst_date_col = ['datetime']
lst_col_to_add = [col.name for col
                  in study.participant.__table__.columns if col.name not in lst_col_to_defer]
lst_date_col_index = [lst_col_to_add.index(col) for col in lst_date_col]
lst_numeric_col_index = [lst_col_to_add.index(col) for col in lst_numeric_col]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/randomize_participant', methods=['GET', 'POST'])
def randomize_participant():
    form = urand_forms.FrmRandomizeParticipant()
    if form.validate_on_submit():
        participant = study.participant()
        form.populate_obj(participant)
        pdf_participants = pd.DataFrame([participant.__dict__], index=[0])
        pdf_participants = pdf_participants[[col for col in pdf_participants.columns if col in [c.name for c in study.participant.__table__.columns]]]
        print(pdf_participants)
        study.upload_new_participants(pdf=pdf_participants)
        return redirect(url_for('list_participants'))
    return render_template('frm_randomize_participant.html', participant_form=form)


@app.route('/api/participants', methods=['GET'])
def get_participants():
    if ('api_key' not in request.args):
        return jsonify({'status': 403,
                        'message': "Please pass your API key with your request."})
    if ('study' not in request.args):
        return jsonify({'status': 400,
                        'message': "Please pass a study name with your request."})

    if request.args.get('study') not in config:
        return jsonify({'status': 404,
                        'message': "Requested study does not exist."})
    study = Study(request.args.get('study'))
    df_participants = study.export_history()
    response = {'status': 200,
                'results': df_participants.to_dict(orient='record')
                }
    return jsonify(response)


@app.route('/api/randomize', methods=['GET'])
def get_participants():
    if ('api_key' not in request.args):
        return jsonify({'status': 403,
                        'message': "Please pass your API key with your request."})
    if ('study' not in request.args):
        return jsonify({'status': 400,
                        'message': "Please pass a study name with your request."})

    if request.args.get('study') not in config:
        return jsonify({'status': 404,
                        'message': "Requested study does not exist."})
    if 'id' not in request.args:
        return jsonify({'status': 400,
                        'message': "Please pass the participant id with your request."})
    study = Study(request.args.get('study'))
    lst_factors = list(study.factors.keys())

    for factor in lst_factors:
        if factor not in request.args:
            return jsonify({'status': 400,
                            'message': "Please pass a value for factor {0} with your request.".format(factor)})
        if request.args.get(factor) not in study.factors[factor]:
            return jsonify({'status': 400,
                            'message': "Invalid value supplised for factor {0}. "
                                       "Allowed values are: [{1}].".format(factor,
                                                                           ", ".join(study.factors[factor]))
                            })
    df_participant = pd.DataFrame(dict([('id', request.args.get('id')),
                                        ('user', 'api')] +
                                       [('f_' + factor,
                                         request.args.get(factor)) for factor in lst_factors]),
                                  index=[0])
    study.upload_new_participants(pdf=df_participant)
    df_participant = study.get_participant(request.args.get('id'))
    response = {'status': 200,
                'results': [df_participant.to_dict(orient='record')]
                }
    return jsonify(response)


@app.route('/api/config', methods=['GET'])
def get_config():
    print(config)
    if ('api_key' not in request.args):
        return jsonify({'status': 403,
                        'message': "Please pass your API key with your request."})
    if ('study' not in request.args):
        return jsonify({'status': 400,
                        'message': "Please pass a study name with your request."})

    if request.args.get('study') not in config:
        return jsonify({'status': 404,
                        'message': "Requested study does not exist."})
    study = Study(request.args.get('study'))

    response = {'status': 200,
                'results': [study.get_config()]
                }
    return jsonify(response)


@app.route("/participants", methods=['GET', 'POST'])
def list_participants():
    """List users with DataTables <= 1.10.x."""
    script_plt, div_plt, js_resources, css_resources = plot_utils.plt_factor_treatment_assignments(study)
    return render_template("tbl_participant.html", project=study.study_name,
                           div_plt=div_plt,
                           script_plt=script_plt,
                           js_resources=js_resources,
                           css_resources=css_resources,
                           colnames=[c.info.get('label', c.name) for c in study.participant.__table__.columns
                                     if (c.name not in ['bg_state'])])


@app.route("/dtbl_participants")
def dtbl_participants():
    """Return server side data."""
    # defining columns
    columns = ([ColumnDT(study.participant.__dict__[col], column_name=col,
                         search_method='numeric' if col in lst_numeric_col else (
                             'date' if col in lst_date_col else 'string_contains')) for col in lst_col_to_add])
    # defining the initial query depending on your purpose
    query = study.session.query(*[study.participant.__dict__[c.name]
                                  for c in study.participant.__table__.columns if c not in lst_col_to_defer])

    # GET parameters
    params = request.args.to_dict()

    # instantiating a DataTable for the query and table needed
    row_table = DataTables(params, query, columns)

    # returns what is needed by DataTable
    dct_result = row_table.output_result()
    return jsonify(dct_result)


if __name__ == '__main__':
    app.run(debug=True)
