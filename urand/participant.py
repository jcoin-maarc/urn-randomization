import pickle
import random
from datetime import datetime, timezone

class Participant:

	def __init__(self, id, user, creation_time=None, trt=None, **factors):
		self.seed = pickle.dumps(random.getstate())
		self.datetime = creation_time if (creation_time is not None) else datetime.now(timezone.utc)
		self.id = id
		self.user = user
		self.__dict__.update(factors)
		self.trt = trt