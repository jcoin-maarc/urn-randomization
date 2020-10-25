"""Utilities for interacting with SQLite DB containing study information"""

from urand.config import config
from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, String, Enum, DateTime, PickleType
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import null
from confuse import NotFoundError
import json
import re

clean = lambda s: re.sub('\W|^(?=\d)','_', s)

def config_table(engine, metadata, study_name):
    """Define table holding study configuration"""
    
    table_name = '{}_config'.format(clean(study_name))
    if not engine.dialect.has_table(engine.connect(), table_name):
        Table(table_name, metadata,
              Column('param', String, primary_key=True),
              Column('value', String))
    
    return table_name

def asgmt_table(engine, metadata, study_name):
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
                     Column('seed', PickleType, nullable=False)])
        
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
            config_tbl(param='alpha', value=alpha),
            config_tbl(param='beta', value=beta),
            config_tbl(param='starting_seed', value=starting_seed),
            config_tbl(param='D', value=D),
            config_tbl(param='urn_selection', value=urn_selection),
            config_tbl(param='treatments', value=json.dumps(treatments)),
            config_tbl(param='factors', value=json.dumps(factors))
        ])
        
        session.commit()

def get_tables(study_name):
    """Return study tables, initializing if necessary"""
    
    try:
        engine = create_engine(config[study_name]['db'].get())
    except NotFoundError:
        engine = create_engine(config['db'].get())
    
    metadata = MetaData()
    
    config_table_name = config_table(engine, metadata, study_name)
    asgmt_table_name = asgmt_table(engine, metadata, study_name)
    
    metadata.reflect(engine)
    
    Base = automap_base(metadata=metadata)
    Base.prepare()
    metadata.create_all(engine)
    
    config_tbl = getattr(Base.classes, config_table_name)
    asgmt_tbl = getattr(Base.classes, asgmt_table_name)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    populate_config(study_name, config_tbl, session)
    
    return (config_tbl, asgmt_tbl, session)

def get_param(tbl, session, param):
    """Retrieve value of parameter from configuration table"""
    
    return session.query(tbl).filter_by(param=param).first().value