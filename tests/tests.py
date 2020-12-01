from urand import Study, db
import os
import numpy as np
import pandas as pd
import pickle
import shutil
import importlib
import urand
import ast
from multiprocessing import Pool

def cleanup_db_after_tests(study):
	study.session.close()
	os.remove(study.db_fname)

def test_upload_with_seed():
	study = Study('Test Study', 'test.db')
	df_file = pd.read_csv(os.path.join('data', 'test_asgmts_with_seed.csv'))
	del df_file['trial_no']
	del df_file['starting_seed']
	df_file.to_csv(os.path.join('data', 'test_asgmts_with_seed.csv'), index=False)
	study.upload_existing_history(os.path.join('data', 'test_asgmts_with_seed.csv'))
	df_participants = db.fetch_participants(study.participant, study.session)
	assert df_participants.shape[0] == df_file.shape[0], "Uploading file with seed unsuccessful"
	cleanup_db_after_tests(study)
	return True

def test_upload_without_seed():
	study = Study('Test Study', 'test.db')
	df_file = pd.read_csv(os.path.join('data', 'test_asgmts_without_seed.csv'))
	study.upload_existing_history(os.path.join('data', 'test_asgmts_without_seed.csv'))
	df_participants = db.fetch_participants(study.participant, study.session)
	assert df_participants.shape[0] == df_file.shape[0], "Uploading file without seed unsuccessful"
	cleanup_db_after_tests(study)
	return True

def simulate_assignments(n_participants, n_simulations, factor_combination_seed, starting_seed,
                         simulation_label, fixed_participants=True):
	"""
	Simulates n_simulations assignments, each with n_participants participants.
	Assignment data is exported to simulation_label as csv files.
	:param n_participants: No. of participants in each trial
	:param n_simulations: No. of trials
	:param factor_combination_seed: Seed fpr participant factor combination subsetting for the first trial
	:param starting_seed: Starting seed for participant assignment for the first trial
	:param simulation_label: Exported data location
	:param fixed_participants: Flag, indicating whether all the trials make use of the same set of participants
	:return:
	"""
	simulation_data_folder = os.path.join('data', 'simulations', str(simulation_label))
	if os.path.exists(simulation_data_folder) and os.path.isdir(simulation_data_folder):
		shutil.rmtree(simulation_data_folder)
	os.mkdir(simulation_data_folder)
	if fixed_participants:
		study = Study('Test Study', 'test.db')
		study.starting_seed = starting_seed
		study.generate_dummy_participants(n_participants, factor_combination_seed)
		study.export_history(os.path.join(simulation_data_folder, 'participants.csv'))
		pdf_participants = pd.read_csv(os.path.join(simulation_data_folder, 'participants.csv'),
			                             dtype=object, encoding='utf8')
		pdf_participants = pdf_participants[['id'] + ['f_' + factor for factor in sorted(study.factors.keys())] +
							['user']]
		pdf_participants.to_csv(os.path.join(simulation_data_folder, 'participants.csv'),
		                                                 index=False)
		cleanup_db_after_tests(study)
	for trial in range(n_simulations):
		process_isolated_trial(starting_seed, factor_combination_seed,
		                       trial, n_participants, simulation_data_folder,
		                       fixed_participants)
		factor_combination_seed = np.random.default_rng(factor_combination_seed).integers(low=1, high=50000, size=1)[0]
		pdf_asgmt = pd.read_csv(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial)),
		                        dtype=object, encoding='utf8')
		pdf_asgmt = pdf_asgmt.assign(seed=pdf_asgmt['seed'].apply(ast.literal_eval))
		starting_seed = pickle.loads(pdf_asgmt.seed.iat[-1]).randint(low=1, high=50000, size=1)[0]


def process_isolated_trial(trial_starting_seed, trial_factor_combination_seed,
                           trial_no, n_participants, simulation_data_folder,
                           fixed_participants):
	study = urand.Study('Test Study', os.path.join(simulation_data_folder, 'test_{0}.db'.format(trial_no)))
	study.starting_seed = trial_starting_seed
	if fixed_participants:
		study.upload_new_participants(file=os.path.join(simulation_data_folder, 'participants.csv'))
	else:
		study.generate_dummy_participants(n_participants, trial_factor_combination_seed)
	study.export_history(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial_no)))
	pdf_trial_data = pd.read_csv(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial_no)),
	                             dtype=object, encoding='utf8')
	pdf_trial_data['trial_no'] = trial_no
	pdf_trial_data['starting_seed'] = trial_starting_seed
	pdf_trial_data.to_csv(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial_no)),
	                      index=False)
	cleanup_db_after_tests(study)

def simulate_assignments_mproc(n_participants, n_simulations, factor_combination_seed, starting_seed, simulation_label, nproc=4,
                               fixed_participants=True):
	simulation_data_folder = os.path.join('data', 'simulations', str(simulation_label))
	if os.path.exists(simulation_data_folder) and os.path.isdir(simulation_data_folder):
		shutil.rmtree(simulation_data_folder)
	os.mkdir(simulation_data_folder)

	if fixed_participants:
		study = Study('Test Study', 'test.db')
		study.starting_seed = starting_seed
		study.generate_dummy_participants(n_participants, factor_combination_seed)
		study.export_history(os.path.join(simulation_data_folder, 'participants.csv'))
		pdf_participants = pd.read_csv(os.path.join(simulation_data_folder, 'participants.csv'),
			                             dtype=object, encoding='utf8')
		pdf_participants = pdf_participants[['id'] + ['f_' + factor for factor in sorted(study.factors.keys())] +
							['user']]
		pdf_participants.to_csv(os.path.join(simulation_data_folder, 'participants.csv'),
		                                                 index=False)
		cleanup_db_after_tests(study)

	lst_trial_seed = np.random.default_rng(starting_seed).integers(low=1, high=50000, size=n_simulations)
	lst_factor_combination_seed = np.random.default_rng(factor_combination_seed).integers(low=1, high=50000,
	                                                                                      size=n_simulations)



	lst_paramsets = list(zip(lst_trial_seed,
	                         lst_factor_combination_seed,
	                         list(range(1, n_simulations + 1)),
	                         [n_participants] * n_simulations,
	                         [simulation_data_folder] * n_simulations,
	                         [fixed_participants]* n_simulations
	                         ))

	mproc_pool = Pool(nproc)
	mproc_pool.starmap(process_isolated_trial, lst_paramsets)
	return 0



if __name__ == '__main__':
	test_upload_with_seed()
	test_upload_without_seed()
	simulate_assignments(30, 4, 100, 100,
	                     1, fixed_participants=True)
	simulate_assignments_mproc(30, 4, 100, 100, 1, nproc=4, fixed_participants=False)


