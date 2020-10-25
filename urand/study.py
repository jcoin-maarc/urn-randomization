"""Urn randomization for group assignment in randomized experiments"""

from urand.config import config
from urand import db
import json

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
    
    def print_config(self):
        attrs = ['study_name', 'w', 'alpha', 'beta', 'starting_seed', 'D',
                 'urn_selection', 'treatments', 'factors']
        for attr in attrs:
            print('{}: {}'.format(attr, getattr(self, attr)))
    
    def get_urns(self, participant):
        """Get urns required to randomize participant
        
        Build list of urns from assignment history.
        """
        pass
    
    def load_history(self, file):
        """Load existing history from study that has already started recruiting"""
        pass
    
    def randomize(self, participant):
        """Randomize participant"""
        pass
