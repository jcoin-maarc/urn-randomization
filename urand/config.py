"""Utilities shared across modules"""

import confuse
import os

config = confuse.LazyConfig('UrnRandomization', __name__)
# Allow config.yaml at project root with highest priority
if os.path.isfile('config.yaml'):
    config.set_file('config.yaml')
