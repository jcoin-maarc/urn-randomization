"""Urn randomization for group assignment in randomized experiments"""

from urand.config import config
from urand import db
import json
import random
import numpy as np
from itertools import product
from datetime import datetime, timezone
import pickle
import ast
import pandas as pd

class Study:
    """Study for which treatments are to be assigned"""
    
    def __init__(self, study_name):
        
        self.study_name = study_name
        config, self.participant, self.session = db.get_tables(study_name)
        
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

    def get_seed(self):
        """Returns the latest state of the random number generator. Returns a random state with study's
        starting seed as the seed for the first patient"""
        seed = db.get_seed(self.participant, self.session)
        if seed is None:
            random.seed(self.starting_seed)
            return pickle.dumps(np.random.RandomState(self.starting_seed))
        else:
            return seed.seed

    def generate_dummy_participants(self, n_participants, seed):
        """Adds dummy participants to study database for using in development mode"""
        nprandom = np.random.RandomState(seed=seed)
        lst_factorlevels = [self.factors[factor] for factor in sorted(self.factors.keys())] #+ [self.treatments]
        lst_factor_combos = list(set(product(*lst_factorlevels)))
        lstdct_participants = [dict([(factor, tpl_participant[factor_index])
                                     for factor_index, factor in enumerate(lst_factor)] +
                                    [('user', 'dummy'),
                                     # ('datetime', datetime.now(timezone.utc)),
                                     # ('seed', pickle.dumps(np.random.RandomState()))
                                     ]
                                    ) for lst_factor, tpl_participant in
                                            product([['f_' + factor
                                                      for factor in sorted(self.factors.keys())] +
                                                     ['id']],
                                                     [tpl + (idx,) for idx, tpl in
                                                      enumerate([lst_factor_combos[i] for i in
                                                                 nprandom.choice(len(lst_factor_combos), n_participants,
                                                                                 replace=True)])])]
        for dct in lstdct_participants:
            dct_participant = dict(dct)
            dct_participant['datetime'] = datetime.now(timezone.utc)
            self.randomize(self.participant(**dct_participant))



    
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
        pdf_urn_assignments = pd.DataFrame([{'factor': factor,
                                  'factor_level': dct_factors["f_" + factor],
                                  'trt': trt,
                                  'n_assignments': 0}
                                 for factor, trt in product(list(self.factors.keys()),
                                                            self.treatments)])

        pdf_asgmts = db.fetch_participants(self.participant, self.session, **dct_factors)
        pdf_urn_assignments = pd.concat([pd.concat([pdf_asgmts[['f_' + factor, 'trt']]
                                        .loc[pdf_asgmts['f_' + factor] == dct_factors["f_" + factor]]
                                        .rename(columns={'f_' + factor: 'factor_level'})
                                        .assign(factor=factor)
                                                for factor in self.factors]
                                        ).groupby(['factor', 'factor_level', 'trt'])\
                                         .size().reset_index().rename(columns={0: 'n_assignments'}),
                                pdf_urn_assignments],
                             ignore_index=True)\
                        .groupby(['factor', 'factor_level', 'trt'])['n_assignments'].sum().reset_index(drop=False)
        pdf_urn_assignments = pdf_urn_assignments.pivot_table(index=['factor', 'factor_level'],
                                        columns=['trt'],
                                        values=['n_assignments'])

        pdf_urn_assignments.columns = [(i[0] + '_' + i[1]).replace('n_assignments', 'trt') for i in pdf_urn_assignments.columns]
        pdf_urn_assignments = pdf_urn_assignments.reset_index()
        lst_trt_col = ['trt_' + trt for trt in self.treatments]
        lst_balls_col = ['balls_trt_' + trt for trt in self.treatments]
        pdf_urns = pdf_urn_assignments.assign(
            **dict([("balls_" + col,
                     self.w +
                     (self.alpha * pdf_urn_assignments[col]) +
                     (self.beta * (pdf_urn_assignments[lst_trt_col].sum(axis=1) - pdf_urn_assignments[col])))
                    for col in lst_trt_col]))
        pdf_urns = pdf_urns.assign(total_balls =
                                   pdf_urns[lst_balls_col].sum(axis=1))
        return pdf_urns


    def export_history(self, file):
        """Exports patient assignment history table as a csv file"""
        db.fetch_participants(self.participant, self.session).to_csv(file, index=False)

    def upload_existing_history(self, file):
        """Load existing history from study that has already started recruiting"""
        pdf_asgmt = pd.read_csv(file, dtype=object, encoding='utf8')
        assert all([a == b for a, b in zip(sorted([col for col in pdf_asgmt.columns if col != 'seed']),
                                           sorted(['id', 'user', 'trt', 'datetime'] +
                                                  ['f_' + factor for factor in self.factors]))]), \
            "Input file does not match study schema"
        pdf_asgmt = pdf_asgmt.assign(datetime = pd.to_datetime(pdf_asgmt['datetime'],
                                                               utc=True))
        if 'seed' in pdf_asgmt.columns:
            pdf_asgmt = pdf_asgmt.assign(seed=pdf_asgmt['seed'].apply(ast.literal_eval))
            db.populate_participants(self.participant, pdf_asgmt.to_dict('records'), self.session, )
        else:
            lstdct_participants = pdf_asgmt.to_dict('records')
            db.populate_participants(self.participant, lstdct_participants[:(pdf_asgmt.shape[0] - 1)], self.session, )
            dct_participant = lstdct_participants[pdf_asgmt.shape[0] - 1]
            dct_participant['seed'] = pickle.dumps(np.random.RandomState(self.starting_seed))
            db.populate_participants(self.participant, [dct_participant], self.session, )

        return


    def upload_new_participants(self, **dct_participants):

        assert ('file' in dct_participants) | ('pdf' in dct_participants), 'Neither filename nor dataframe eith patient ' \
                                                                           'info provided as input'
        pdf_asgmt = dct_participants['pdf'] if ('pdf' in dct_participants) else pd.read_csv(dct_participants['file'],
                                                                                            dtype=object,
                                                                                            encoding='utf8')
        assert all([a == b for a, b in zip(sorted(pdf_asgmt.columns),
                                           sorted(['id', 'user', ] +
                                                  ['f_' + factor for factor in self.factors]))]), \
            "Input file does not match study schema"

        lstdct_participants = pdf_asgmt.to_dict('records')
        for dct in lstdct_participants:
            dct_participant = dict(dct)
            dct_participant['datetime'] = datetime.now(timezone.utc)
            self.randomize(self.participant(**dct_participant))
        return

    def randomize(self, participant):
        """Randomize participant
            * Calculates d (level of imbalance) for all urns the patient is a candidate for
            * picks the urn with the least imbalance (ties are broken with random selection)
                with probability p_l as per urn_selection method
            * Randomly picks one of the treatment balls, k_i, in the selected urn
            * Patient is then assigned to the treatment type represented by the ball
        """

        pdf_urns = self.get_urns(participant)
        participant.seed = self.get_seed()
        lst_balls_col = ['balls_trt_' + trt for trt in self.treatments]
        if self.D == 'range':
            pdf_urns = pdf_urns.assign(d = (pdf_urns[lst_balls_col].max(axis=1) - pdf_urns[lst_balls_col].min(axis=1))
                                                .div(pdf_urns['total_balls']))
        else:
            pdf_urns = pdf_urns.assign(d=(pdf_urns[lst_balls_col].var(axis=1)).div(pdf_urns['total_balls']))
        ### Selecting the urn with the most imbalance
        nprandom = pickle.loads(participant.seed)
        ### Getting the urns with maximum imbalance and sorting them by factor columns
        pdf_candidate_urns = pdf_urns.loc[pdf_urns['d']==pdf_urns['d'].max()
                                        ].sort_values(by=['factor'],
                                                      ascending=True).reset_index(drop=True)
        pdf_selected_urn = pdf_candidate_urns.iloc[[nprandom.choice(pdf_candidate_urns.index.tolist(), 1,
                                                                  replace=True
                            )[0]]]
        trt = nprandom.choice(lst_balls_col, 1,
                            replace=True,
                            p = pdf_selected_urn[lst_balls_col].div(pdf_selected_urn['total_balls'].values,
                                                                    axis=0).values.flatten().tolist()
                            )[0]
        trt = trt.replace('balls_trt_', '')
        participant.trt = trt
        participant.seed = pickle.dumps(nprandom)
        db.populate_participant(self.participant, participant, self.session, )
        return participant
