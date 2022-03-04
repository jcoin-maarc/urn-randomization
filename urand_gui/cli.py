import click
import secrets
import pandas as pd
from sqlalchemy.orm.exc import NoResultFound
from flask.cli import with_appcontext
from urand_gui.models import db, User, Study
from urand_gui import urand_config
from flask.cli import AppGroup


@click.group()
def cli():
    pass


@cli.command(name="createdb")
@with_appcontext
def create_db():
    """Initializes flask app DB with available studies & creates user tables"""
    db.create_all()
    db.session.commit()
    print("Database tables created")

    for key in urand_config:
        if key not in ["db", "w", "alpha", "beta", "D", "urn_selection"]:
            query = Study.query.filter_by(name=key)
            try:
                ety_study = query.one()
            except NoResultFound:
                ety_study = Study()
                ety_study.name = key
                db.session.add(ety_study)
                db.session.commit()


@cli.command(name="add_user")
@click.argument("uname")
@click.argument("email")
@with_appcontext
def add_user(uname, email):
    """Adds a user"""
    user = User()
    user.username = uname
    user.email = email
    user.api_key = secrets.token_hex(32)
    try:
        db.session.add(user)
        db.session.commit()
        print("User added to database")
    except Exception as ex:
        print(ex)


@cli.command(name="list_users")
@with_appcontext
def list_users():
    """Lists available users"""
    pd.options.display.max_colwidth = 1000
    pdf_user = pd.read_sql(User.query.statement, db.session.bind)
    print(pdf_user)


@cli.command(name="delete_user")
@click.argument("email")
@with_appcontext
def delete_user(email):
    """Deletes user linked to email"""
    query = User.query.filter_by(email=email)
    try:
        ety_user = query.one()
        db.session.delete(ety_user)
        db.session.commit()
        print("Successfully deleted user")
    except NoResultFound:
        print("User not found")


if __name__ == "__main__":
    cli(obj={})
