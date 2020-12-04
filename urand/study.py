"""Urn randomization for group assignment in randomized experiments"""

from urand.config import config
from urand import db
import json
import random
from numpy.random import Generator, PCG64
from itertools import product
from datetime import datetime, timezone
import ast
import pandas as pd

class Study:
    """Study for which treatments are to be assigned"""
    
    def __init__(self, study_name, memory=False):
        
        self.study_name = study_name
        config, self.participant, self.session = db.get_tables(study_name, memory)
        
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

    def get_bg_state(self):
        """Returns last state of NumPy BitGenerator
        
        This is equal to the state after the last assignment, or the state
        after initialization with the study's random number seed before any
        assignments have been made.
        """
        last_state = db.get_last_state(self.participant, self.session)
        if not last_state:
            bg = PCG64(self.starting_seed)
            return bg.state
        else:
            return last_state.bg_state
    
    def generate_dummy_participants(self, n_participants, seed):
        """Adds dummy participants to study database for using in development mode"""
        rng = Generator(PCG64(seed))
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
                                                                 rng.choice(len(lst_factor_combos), n_participants,
                                                                            replace=True)])])]
        for dct in lstdct_participants:
            dct_participant = dict(dct)
            dct_participant['datetime'] = datetime.now(timezone.utc)
            self.randomize(self.participant(**dct_participant))
        return


    
    def print_config(self):
        attrs = ['study_name', 'w', 'alpha', 'beta', 'starting_seed', 'D',
                 'urn_selection', 'treatments', 'factors']
        for attr in attrs:
            return '{}'.format(getattr(self, attr))
    
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

        pdf_asgmts = db.get_participants(self.participant, self.session, **dct_factors)
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
        db.get_participants(self.participant, self.session).to_csv(file, index=False)

    def upload_existing_history(self, file):
        """Load existing history from study that has already started recruiting"""
        pdf_asgmt = pd.read_csv(file, dtype=object, encoding='utf8')
        assert all([a == b for a, b in zip(sorted([col for col in pdf_asgmt.columns if col != 'bg_state']),
                                           sorted(['id', 'user', 'trt', 'datetime'] +
                                                  ['f_' + factor for factor in self.factors]))]), \
            "Input file does not match study schema"
        pdf_asgmt = pdf_asgmt.assign(datetime = pd.to_datetime(pdf_asgmt['datetime'],
                                                               utc=True))
        if 'bg_state' in pdf_asgmt.columns:
            pdf_asgmt = pdf_asgmt.assign(bg_state=pdf_asgmt['bg_state'].apply(ast.literal_eval))
            db.add_participants(self.participant, pdf_asgmt.to_dict('records'), self.session, )
        else:
            lstdct_participants = pdf_asgmt.to_dict('records')
            db.add_participants(self.participant, lstdct_participants[:(pdf_asgmt.shape[0] - 1)], self.session, )
            dct_participant = lstdct_participants[pdf_asgmt.shape[0] - 1]
            dct_participant['bg_state'] = PCG64(self.starting_seed).state
            db.add_participants(self.participant, [dct_participant], self.session, )

        return

    ## TODO: get study status - multiple studies, npatients, print urn assignments
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
        """Randomize new participant
        
        1. Calculate d (level of imbalance) for all urns matching participant's
           characteristics
        2. Pick the urn with the least imbalance (ties are broken with random
           selection) with probability p_l as per urn_selection method
        3. Randomly pick one of the treatment balls, k_i, in the selected urn
        4. Participant assigned to the treatment type represented by the ball
        """
        
        # Initialize RNG
        bg = PCG64()
        bg.state = self.get_bg_state()
        rng = Generator(bg)
        
        urns = self.get_urns(participant)
        lst_balls_col = ['balls_trt_' + trt for trt in self.treatments]
        if self.D == 'range':
            urns = urns.assign(d=(urns[lst_balls_col].max(axis=1) -
                                  urns[lst_balls_col].min(axis=1))
                                 .div(urns['total_balls']))
        else:
            urns = urns.assign(d=(urns[lst_balls_col].var(axis=1))
                                 .div(urns['total_balls']))
        
        # Select urn with most imbalance
        # Get urns with maximum imbalance and sort them by factor columns
        candidate_urns = urns.loc[urns['d']==urns['d'].max()
                                 ].sort_values(by=['factor'],
                                               ascending=True).reset_index(drop=True)
        selected_urn = candidate_urns.iloc[[rng.choice(candidate_urns.index.tolist(),
                                                       1, replace=True)[0]]]
        trt = rng.choice(lst_balls_col, 1,
                         replace=True,
                         p = selected_urn[lst_balls_col].div(selected_urn['total_balls'].values,
                                                             axis=0).values.flatten().tolist()
                        )[0]
        trt = trt.replace('balls_trt_', '')
        participant.trt = trt
        participant.datetime = datetime.now(timezone.utc)
        participant.bg_state = bg.state
        db.add_participant(participant, self.session)
        return participant
