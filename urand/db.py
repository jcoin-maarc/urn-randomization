"""Utilities for interacting with SQLite DB containing study information"""

import json
import re

from confuse import NotFoundError
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Table, Column, String, Enum, DateTime, PickleType, or_
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import null
import pandas as pd

from urand.config import config

clean = lambda s: re.sub('\W|^(?=\d)','_', s)

def config_table(engine, metadata, study_name):
    """Define table holding study configuration"""
    
    table_name = '{}_config'.format(clean(study_name))
    if not engine.dialect.has_table(engine.connect(), table_name):
        Table(table_name, metadata,
              Column('param', String, primary_key=True),
              Column('value', String))
    
    return table_name

def participant_table(engine, metadata, study_name):
    """Define table holding history of treatment assignments"""
    
    table_name = '{}_history'.format(clean(study_name))
    if not engine.dialect.has_table(engine.connect(), table_name):
        
        try:
            trts = config[study_name]['treatments'].get()
            factors = config[study_name]['factors'].get()
        except NotFoundError:
            print('Treatments or factors not found in configuration file')
            raise
        
        cols = [Column('id', String, primary_key=True)]
        for factor in factors:
            cols.append(Column('f_' + str(factor),
                               Enum(*[str(i) for i in factors[factor]],
                                    validate_strings=True),
                               nullable=False))
        cols.extend([Column('trt', Enum(*[str(t) for t in trts]), nullable=False),
                     Column('datetime', DateTime, nullable=False),
                     Column('user', String, nullable=False),
                     Column('seed', PickleType, nullable=True)])
        
        Table(table_name, metadata, *cols)
    
    return table_name

def populate_config(study_name, config_tbl, session):
    """Populate or verify config table
    
    Populate config table with values from config file or check consistency
    with parameters specified in study block, if available.
    """
    
    if session.query(config_tbl).first():
        # TODO Verify consistency with study block in config file, if available
        pass
        
    else:
        study_config = config[study_name]
        
        # TODO Allow w, alpha and beta to be sequence of integers
        w = (study_config['w'].get(int) if 'w' in study_config
                 else config['w'].get(int))
        alpha = (study_config['alpha'].get(int) if 'alpha' in study_config
                 else config['alpha'].get(int))
        beta = (study_config['beta'].get(int) if 'beta' in study_config
                else config['beta'].get(int))
        D = (study_config['D'].as_choice(['range','variance'])
             if 'D' in study_config
             else config['D'].as_choice(['range','variance']))
        urn_selection = (study_config['urn_selection'].as_choice(['method1'])
                         if 'urn_selection' in study_config
                         else config['urn_selection'].as_choice(['method1']))
        
        try:
            starting_seed = config[study_name]['starting_seed'].get(int)
        except NotFoundError:
            starting_seed = null()
        
        try:
            treatments = [str(t) for t in config[study_name]['treatments'].get()]
            factors = config[study_name]['factors'].get()
            for factor in factors:
                factors[factor] = [str(f) for f in factors[factor]]
        except NotFoundError:
            print('Treatments or factors not found in configuration file')
            raise
        
        session.add_all([
            config_tbl(param='w', value=w),
            config_tbl(param='alpha', value=alpha),
            config_tbl(param='beta', value=beta),
            config_tbl(param='starting_seed', value=starting_seed),
            config_tbl(param='D', value=D),
            config_tbl(param='urn_selection', value=urn_selection),
            config_tbl(param='treatments', value=json.dumps(treatments)),
            config_tbl(param='factors', value=json.dumps(factors))
        ])
        
        session.commit()


def populate_participants(participant_tbl, lstdct_participant, session):
    """Populate asgmt table

    """
    try:
        session.add_all([participant_tbl(**dct_participant) for dct_participant in lstdct_participant])
        session.commit()
    except IntegrityError as ex:
        print(ex)



def populate_participant(participant_tbl, participant, session):
    """Populate asgmt table

    """
    try:
        session.add(participant)
        session.commit()
    except IntegrityError as ex:
        print(ex)

def get_tables(study_name, db_fname=None):
    """Return study tables, initializing if necessary"""
    db_url = 'sqlite:///' + db_fname if db_fname else (
        config[study_name]['db'].get() if (study_name in config) else config['db'].get())
    engine = create_engine(db_url)

    # try:
    #     engine = create_engine(config[study_name]['db'].get())
    # except NotFoundError:
    #     engine = create_engine(config['db'].get())
    
    metadata = MetaData()
    
    config_table_name = config_table(engine, metadata, study_name)
    participant_table_name = participant_table(engine, metadata, study_name)
    
    metadata.reflect(engine)
    
    Base = automap_base(metadata=metadata)
    Base.prepare()
    metadata.create_all(engine)
    
    config_tbl = getattr(Base.classes, config_table_name)
    participant_tbl = getattr(Base.classes, participant_table_name)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    populate_config(study_name, config_tbl, session)
    
    return (config_tbl, participant_tbl, session)

def fetch_participants(participant_table, session, **factorlevels):
    """Retrieve assignments from the db. Filter by factor values, if present"""
    query = session.query(participant_table)
    query = query.filter(or_(*[getattr(participant_table, attr) == value for attr, value in factorlevels.items()]))
    pdf_results = pd.read_sql(query.statement, session.bind)
    return pdf_results


def get_seed(participant_table, session):
    query = session.query(participant_table.seed).order_by(participant_table.datetime.desc())
    return query.first()


def get_param(tbl, session, param):
    """Retrieve value of parameter from configuration table"""
    return session.query(tbl).filter_by(param=param).first().value
