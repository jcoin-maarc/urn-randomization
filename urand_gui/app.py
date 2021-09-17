# -*- coding: utf-8 -*-
from flask import flash, redirect, url_for, render_template, request,  jsonify, render_template, request, Response
from flask_wtf import CSRFProtect
from flask_login import login_required, logout_user, current_user


from datatables import ColumnDT, DataTables

from flask_bootstrap import Bootstrap

import pandas as pd
import urand_gui.forms as urand_forms
import urand_gui.plots as plot_utils
from urand_gui.models import User

from urand_gui import study, Study, config, app, login_manager

# app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'lumen'  # uncomment this line to test bootswatch theme

#bootstrap_app = Bootstrap(app)
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


@login_manager.request_loader
def load_user(request):
    """Attempt to authenticate user using API key"""

    api_key = request.form.get('api_key')
    if api_key:
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user

    return None


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out')
    return redirect(url_for('index'))


@login_manager.unauthorized_handler
def unauthorized():
    """Respond to unauthorized requests"""

    if request.form.get('api_key'):
        return jsonify({"message": "Unauthorized request"}), 401

    return redirect(url_for('index'))


# TODO: Fetch username from currentusername
@app.route('/randomize_participant', methods=['GET', 'POST'])
@login_required
def randomize_participant():
    """This function renders Randomize Participant form with which the end user can randomize new participants
    """
    form = urand_forms.FrmRandomizeParticipant(user=current_user.username)
    if form.validate_on_submit():
        participant = study.participant()
        form.populate_obj(participant)
        pdf_participants = pd.DataFrame([participant.__dict__], index=[0])
        pdf_participants = pdf_participants[[col for col in pdf_participants.columns
                                             if col in [c.name for c in study.participant.__table__.columns]]]
        study.upload_new_participants(pdf=pdf_participants)
        pdf_participant = study.get_participant(participant.id)
        flash("Participant id {0} has been randomized to treatment {1}".format(pdf_participant['id'].values[0],
                                                                               pdf_participant['trt'].values[0]),
              category="info")
        return redirect(url_for('list_participants'))
    return render_template('frm_randomize_participant.html', participant_form=form)


@app.route('/study_participants', methods=['GET'])
@login_required
def api_get_participants():
    """
    .. http:get:: /study_participants

        Return list of study participants with their factor levels and treatment assignments

        **Example request**:

        .. sourcecode:: http

            GET /study_participants HTTP/1.1
            Host: https://rcg.bsd.uchicago.edu/urand

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
                "message":"Success",
                "results":[
                    {
                        "bg_state":{
                            "bit_generator":"PCG64",
                            "has_uint32":1,
                            "state":{
                                "inc":30008503642980956324491363429807189605,
                                "state":164404244729103591598495580972637239091
                            },
                            "uinteger":3586218795
                        },
                        "datetime":"Wed, 10 Feb 2021 00:01:08 GMT",
                        "f_african_american":"Yes (including mixed)",
                        "f_crime_violence_screener_count":"Low",
                        "f_electronic_monitoring":"Yes",
                        "f_hispanic_descent":"Other",
                        "f_incarceration_days":"Moderate (13-90)",
                        "f_local_site":"40-Grundy County",
                        "f_prior_opioid_overdose":"Yes",
                        "f_prior_substance_use_treatment":"Any other SUD treatment",
                        "f_probation_parole_community_supervision":"Other",
                        "f_sex":"Male",
                        "f_substance_screener_symptoms":"High (3-5)",
                        "f_substance_use_days":"High",
                        "f_young_adult":"Other (26 or older)",
                        "id":"0",
                        "trt":"RMC-Q",
                        "user":"dummy"
                    },
                    {
                        "bg_state":{
                            "bit_generator":"PCG64",
                            "has_uint32":0,
                            "state":{
                                "inc":30008503642980956324491363429807189605,
                                "state":175296851311552035585228848780835049764
                            },
                            "uinteger":3586218795
                        },
                        "datetime":"Wed, 10 Feb 2021 00:01:08 GMT",
                        "f_african_american":"No",
                        "f_crime_violence_screener_count":"Moderate (1-2)",
                        "f_electronic_monitoring":"Yes",
                        "f_hispanic_descent":"Yes",
                        "f_incarceration_days":"Low (0-12)",
                        "f_local_site":"70-Will County",
                        "f_prior_opioid_overdose":"Yes",
                        "f_prior_substance_use_treatment":"Any other SUD treatment",
                        "f_probation_parole_community_supervision":"Other",
                        "f_sex":"Male",
                        "f_substance_screener_symptoms":"Moderate (1-2)",
                        "f_substance_use_days":"Moderate (13-44)",
                        "f_young_adult":"Yes (18-25)",
                        "id":"1",
                        "trt":"MART",
                        "user":"dummy"
                    }
                ],
                "status":200
            }

        :query api_key: API Key
        :query study: study name
        :query id: participant id
        :query factor: Factor value. All study factor levels should be passed
        :resheader Content-Type: application/json
        :statuscode 200: participnts found for study
        :statuscode 400: Invalid request
        :statuscode 401: Unauthorized access
        :statuscode 404: Study not found
        :return: (status Status code, message Status message/ error info, List of participants)
        :rtype: (str, str, list)
    """
    dct_data = {}
    status = 200
    if ('api_key' not in request.args):
        status = 401
        dct_data['message'] = "Please pass your API key with your request."
    elif ('study' not in request.args):
        status = 400
        dct_data['message'] = "Please pass a study name with your request."

    elif request.args.get('study') not in config:
        status = 404
        dct_data['message'] = "Requested study does not exist."
    else:
        study = Study(request.args.get('study'))
        df_participants = study.export_history()
        dct_data['message'] = 'Success'
        dct_data['results'] = df_participants.to_dict(orient='record')
    dct_data['status'] = status
    return jsonify(dct_data), status


@csrf.exempt
@app.route('/study_participants', methods=['POST'])
@login_required
def api_randomize_participant():
    """
    .. http:post:: /study_participants

        Randomize a new participant

        **Example request**:

        .. sourcecode:: http

          POST /study_participants HTTP/1.1
          Host: https://rcg.bsd.uchicago.edu/urand

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json

            {
               "message":"Success",
               "results":[
                  {
                     "bg_state":{
                        "bit_generator":"PCG64",
                        "has_uint32":1,
                        "state":{
                           "inc":30008503642980956324491363429807189605,
                           "state":164404244729103591598495580972637239091
                        },
                        "uinteger":3586218795
                     },
                     "datetime":"Wed, 10 Feb 2021 00:01:08 GMT",
                     "f_african_american":"Yes (including mixed)",
                     "f_crime_violence_screener_count":"Low",
                     "f_electronic_monitoring":"Yes",
                     "f_hispanic_descent":"Other",
                     "f_incarceration_days":"Moderate (13-90)",
                     "f_local_site":"40-Grundy County",
                     "f_prior_opioid_overdose":"Yes",
                     "f_prior_substance_use_treatment":"Any other SUD treatment",
                     "f_probation_parole_community_supervision":"Other",
                     "f_sex":"Male",
                     "f_substance_screener_symptoms":"High (3-5)",
                     "f_substance_use_days":"High",
                     "f_young_adult":"Other (26 or older)",
                     "id":"0",
                     "trt":"RMC-Q",
                     "user":"dummy"
                  },
                  {
                     "bg_state":{
                        "bit_generator":"PCG64",
                        "has_uint32":0,
                        "state":{
                           "inc":30008503642980956324491363429807189605,
                           "state":175296851311552035585228848780835049764
                        },
                        "uinteger":3586218795
                     },
                     "datetime":"Wed, 10 Feb 2021 00:01:08 GMT",
                     "f_african_american":"No",
                     "f_crime_violence_screener_count":"Moderate (1-2)",
                     "f_electronic_monitoring":"Yes",
                     "f_hispanic_descent":"Yes",
                     "f_incarceration_days":"Low (0-12)",
                     "f_local_site":"70-Will County",
                     "f_prior_opioid_overdose":"Yes",
                     "f_prior_substance_use_treatment":"Any other SUD treatment",
                     "f_probation_parole_community_supervision":"Other",
                     "f_sex":"Male",
                     "f_substance_screener_symptoms":"Moderate (1-2)",
                     "f_substance_use_days":"Moderate (13-44)",
                     "f_young_adult":"Yes (18-25)",
                     "id":"1",
                     "trt":"MART",
                     "user":"dummy"
                  }
               ],
               "status":200
            }

        :query api_key: API Key
        :query study: study name
        :query id: participant id
        :query factor: Factor value. All study factor levels should be passed
        :resheader Content-Type: application/json
        :statuscode 200: participnts found for study
        :statuscode 400: Invalid request
        :statuscode 401: Unauthorized access
        :statuscode 404: Study not found
        :return: (status Status code, message Status message/ error info, results Participant info)
        :rtype: (str, str, dict)
    """
    dct_data = {}
    status = 200
    if ('api_key' not in request.args):
        status = 401
        dct_data['message'] = "Please pass your API key with your request."
    elif ('study' not in request.args):
        status = 400
        dct_data['message'] = "Please pass a study name with your request."

    elif request.args.get('study') not in config:
        status = 404
        dct_data['message'] = "Requested study does not exist."
    else:
        if 'id' not in request.args:
            status = 400
            dct_data['message'] = "Please pass the participant id with your request."
        if status == 200:
            study = Study(request.args.get('study'))
            lst_factors = list(study.factors.keys())
            for factor in lst_factors:
                if factor not in request.args:
                    status = 400
                    dct_data['message'] = "Please pass a value for factor {0} with your request.".format(factor)
                    break
                if request.args.get(factor) not in study.factors[factor]:
                    status = 400
                    dct_data['message'] = "Invalid level supplied for factor {0}. " +\
                                          "Allowed level are: [{1}].".format(factor,
                                                                ", ".join(study.factors[factor]))
                    break

            if study.get_participant(request.args.get('id')).shape[0] > 0:
                status = 400
                dct_data['message'] = f"Participant {request.args.get('id')} is already assigned"
                df_participant = study.get_participant(request.args.get('id'))
                dct_data['results'] = df_participant.to_dict(orient='record')
            else:
                df_participant = pd.DataFrame(dict([('id', request.args.get('id')),
                                                    ('user', 'api')] +
                                                   [('f_' + factor,
                                                     request.args.get(factor)) for factor in lst_factors]),
                                              index=[0])
                study.upload_new_participants(pdf=df_participant)
                df_participant = study.get_participant(request.args.get('id'))
                dct_data['message'] = "Success"
                dct_data['results'] = df_participant.to_dict(orient='record')
    dct_data['status'] = status
    return jsonify(dct_data), status


@app.route('/study_config', methods=['GET'])
@login_required
def api_get_config():
    """
    .. http:get:: /study_config

        Return study configuration.

        **Example request**:

            .. sourcecode:: http

              GET /study_config HTTP/1.1
              Host: https://rcg.bsd.uchicago.edu/urand

        **Example response**:

            .. sourcecode:: http

              HTTP/1.1 200 OK
              Vary: Accept
              Content-Type: application/json

              {
                  "message": "Success",
                  "results": {
                    "D": "range",
                    "alpha": 0,
                    "beta": 1,
                    "factors": {
                      "african_american": [
                        "Yes (including mixed)",
                        "No"
                      ],
                      "crime_violence_screener_count": [
                        "Low",
                        "Moderate (1-2)",
                        "High (3-5)"
                      ],
                      "electronic_monitoring": [
                        "Yes",
                        "Other"
                      ],
                      "hispanic_descent": [
                        "Yes",
                        "Other"
                      ],
                      "incarceration_days": [
                        "Low (0-12)",
                        "Moderate (13-90)",
                        "High (91+)"
                      ],
                      "local_site": [
                        "11-Cook County \u2013 Chicago",
                        "30-Dupage County",
                        "40-Grundy County",
                        "50-Mclean County",
                        "60-Tazewell County",
                        "70-Will County"
                      ],
                      "prior_opioid_overdose": [
                        "Yes",
                        "No"
                      ],
                      "prior_substance_use_treatment": [
                        "Any MOUD treatment",
                        "Any other SUD treatment",
                        "Other"
                      ],
                      "probation_parole_community_supervision": [
                        "Yes (1+ days)",
                        "Other"
                      ],
                      "sex": [
                        "Male",
                        "Female"
                      ],
                      "substance_screener_symptoms": [
                        "Low",
                        "Moderate (1-2)",
                        "High (3-5)"
                      ],
                      "substance_use_days": [
                        "Low (0-12)",
                        "Moderate (13-44)",
                        "High"
                      ],
                      "young_adult": [
                        "Yes (18-25)",
                        "Other (26 or older)"
                      ]
                    },
                    "starting_seed": 100,
                    "treatments": [
                      "MART",
                      "RMC-Q",
                      "RMC-A"
                    ],
                    "urn_selection": "method1",
                    "w": 1
                  },
                  "status": 200
                }

    :query api_key: API Key
    :query study: study name
    :resheader Content-Type: application/json
    :statuscode 200: participnts found for study
    :statuscode 400: Invalid request
    :statuscode 401: Unauthorized access
    :statuscode 404: Study not found
    :return: (status Status code, message Status message/ error info, results Study configuration)
    :rtype: (str, str, dict)
            """
    dct_data = {}
    status = 200
    if ('api_key' not in request.args):
        status = 401
        dct_data['message'] = "Please pass your API key with your request."
    elif ('study' not in request.args):
        status = 400
        dct_data['message'] = "Please pass a study name with your request."

    elif request.args.get('study') not in config:
        status = 404
        dct_data['message'] = "Requested study does not exist."
    else:
        study = Study(request.args.get('study'))
        dct_data['message'] = 'Success'
        dct_data['results'] = study.get_config()

    dct_data['status'] = status
    return jsonify(dct_data), status


@app.route("/participants", methods=['GET', 'POST'])
@login_required
def list_participants():
    """List randomized participants"""
    script_plt, div_plt, js_resources, css_resources = plot_utils.plt_factor_treatment_assignments(study)
    return render_template("tbl_participant.html", project=study.study_name,
                           div_plt=div_plt,
                           script_plt=script_plt,
                           js_resources=js_resources,
                           css_resources=css_resources,
                           colnames=[c.info.get('label', c.name) for c in study.participant.__table__.columns
                                     if (c.name not in ['bg_state'])])


@app.route("/dtbl_participants")
@login_required
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
