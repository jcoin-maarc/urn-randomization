from flask import Flask
from flask import render_template
from urand import Study
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
# app.config.from_envvar('app-config.cfg')

study = Study("Example Study")


@app.route("/")
def status():
    study_name = study.print_config()
    return render_template("status.html", study_name=study_name)
