"""Urn randomization for group assignment in randomized experiments"""

from urand.config import config
from urand import db, participant
import json
import random
from itertools import product
from datetime import datetime, timezone
import pickle
import ast
import pandas as pd

class Study:
    """Study for which treatments are to be assigned"""
    
    def __init__(self, study_name):
        
        self.study_name = study_name
        config, self.asgmt, self.session = db.get_tables(study_name)
        
        # TODO Allow w, alpha and beta to be sequence of integers
        self.w = int(db.get_param(config, self.session, 'w'))
        self.alpha = int(db.get_param(config, self.session, 'alpha'))
        self.beta = int(db.get_param(config, self.session, 'beta'))
        starting_seed = db.get_param(config, self.session, 'starting_seed')
        self.starting_seed = (int(starting_seed) if starting_seed else None)
        self.D = db.get_param(config, self.session, 'D')
        self.urn_selection = db.get_param(config, self.session, 'urn_selection')
        self.treatments = json.loads(db.get_param(config, self.session, 'treatments'))
        self.factors = json.loads(db.get_param(config, self.session, 'factors'))

    def generate_dummy_participants(self, n_participants, seed):
        """Adds dummy participants to study database for using in development mode"""
        random.seed(seed)
        lst_factorlevels = [self.factors[factor] for factor in self.factors] + [self.treatments]
        lstdct_participants = [dict([(factor, tpl_participant[factor_index])
                                     for factor_index, factor in enumerate(lst_factor)] +
                                    [('user', 'dummy'),
                                     ('datetime', datetime.now(timezone.utc)),
                                     ('seed', pickle.dumps(random.getstate()))]
                                    ) for lst_factor, tpl_participant in
                                            product([['f_' + factorlevel
                                                      for factorlevel in self.factors.keys()] +
                                                     ['trt', 'id']],
                                                     [tpl + (idx,) for idx, tpl in enumerate(random.sample(set(product(*lst_factorlevels)),
                                                                   n_participants))])]
        db.populate_asgmt(self.asgmt, lstdct_participants, self.session,)



    
    def print_config(self):
        attrs = ['study_name', 'w', 'alpha', 'beta', 'starting_seed', 'D',
                 'urn_selection', 'treatments', 'factors']
        for attr in attrs:
            print('{}: {}'.format(attr, getattr(self, attr)))
    
    def get_urns(self, participant):
        """Get urns required to randomize participant
        
        Build list of urns from assignment history.
        """
        dct_participant = participant.__dict__
        dct_factors = dict((k, dct_participant[k]) for k in dct_participant if k.startswith('f_'))
        pdf_urns = pd.DataFrame([{'factor': factor,
                                  'factor_level': dct_factors["f_" + factor],
                                  'trt': trt,
                                  'n_assignments': 0}
                                 for factor, trt in product(list(self.factors.keys()),
                                                            self.treatments)])

        pdf_asgmts = db.load_asgmt(self.asgmt, self.session, **dct_factors)
        pdf_urns = pd.concat([pd.concat([pdf_asgmts[['f_' + factor, 'trt']]
                                        .loc[pdf_asgmts['f_' + factor] == dct_factors["f_" + factor]]
                                        .rename(columns={'f_' + factor: 'factor_level'})
                                        .assign(factor=factor)
                                                for factor in self.factors]
                                        ).groupby(['factor', 'factor_level', 'trt'])\
                                         .size().reset_index().rename(columns={0: 'n_assignments'}),
                                pdf_urns],
                             ignore_index=True)\
                        .groupby(['factor', 'factor_level', 'trt'])['n_assignments'].sum().reset_index()
        return pdf_urns
    
    def upload_history(self, file):
        """Load existing history from study that has already started recruiting"""
        pdf_asgmt = pd.read_csv(file, dtype=object, encoding='utf8')
        assert all([a == b for a, b in zip(sorted(pdf_asgmt.columns),
                                           sorted(['id', 'user', 'trt', 'datetime', 'seed'] +
                                                  ['f_' + factor for factor in self.factors]))]), \
            "Input file does not match study schema"
        pdf_asgmt = pdf_asgmt.assign(datetime = pd.to_datetime(pdf_asgmt['datetime'],
                                                               utc=True),
                                     seed=pdf_asgmt['seed'].apply(ast.literal_eval))
        db.populate_asgmt(self.asgmt, pdf_asgmt.to_dict('records'), self.session, )

    
    def randomize(self, participant):
        """Randomize participant"""
        pass
