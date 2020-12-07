from urand import Study, db
import os
import numpy as np
from numpy.random import Generator, PCG64
import pandas as pd
import glob
import shutil
import urand
import ast
from multiprocessing import Pool


def test_upload_with_seed():
	study = Study('Test Study', memory=True)
	df_file = pd.read_csv(os.path.join('data', 'test_asgmts_with_seed.csv'))
	study.upload_existing_history(file=os.path.join('data', 'test_asgmts_with_seed.csv'))
	df_participants = db.get_participants(study.participant, study.session)
	assert df_participants.shape[0] == df_file.shape[0], "Uploading file with seed unsuccessful"
	return True

def test_upload_without_seed():
	study = Study('Test Study', memory=True)
	df_file = pd.read_csv(os.path.join('data', 'test_asgmts_without_seed.csv'))
	study.upload_existing_history(file=os.path.join('data', 'test_asgmts_without_seed.csv'))
	df_participants = db.get_participants(study.participant, study.session)
	assert df_participants.shape[0] == df_file.shape[0], "Uploading file without seed unsuccessful"
	return True

def simulate_assignments(n_participants, n_simulations, factor_combination_seed, starting_seed,
                         simulation_label, study_name='Test Study',
                         fixed_participants=True):
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
	os.makedirs(simulation_data_folder)
	if fixed_participants:
		study = Study(study_name, memory=True)
		study.starting_seed = starting_seed
		study.generate_dummy_participants(n_participants, factor_combination_seed)
		study.export_history(os.path.join(simulation_data_folder, 'participants.csv'))
		pdf_participants = pd.read_csv(os.path.join(simulation_data_folder, 'participants.csv'),
			                             dtype=object, encoding='utf8')
		pdf_participants = pdf_participants[['id'] + ['f_' + factor for factor in sorted(study.factors.keys())] +
							['user']]
		pdf_participants.to_csv(os.path.join(simulation_data_folder, 'participants.csv'),
		                                                 index=False)
	for trial in range(n_simulations):
		process_isolated_trial(starting_seed, factor_combination_seed,
		                       trial, n_participants, simulation_data_folder, study_name,
		                       fixed_participants)
		factor_combination_seed = np.random.default_rng(factor_combination_seed).integers(low=1, high=50000, size=1)[0]
		pdf_asgmt = pd.read_csv(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial)),
		                        dtype=object, encoding='utf8')
		pdf_asgmt = pdf_asgmt.assign(bg_state=pdf_asgmt['bg_state'].apply(ast.literal_eval))
		bg = PCG64()
		bg.state = pdf_asgmt.seed.iat[-1]
		rng = Generator(bg)
		starting_seed = rng.integers(low=1, high=50000, size=1)[0]


def process_isolated_trial(trial_starting_seed, trial_factor_combination_seed,
                           trial_no, n_participants, simulation_data_folder, study_name='Test Study',
                           fixed_participants=True):
	study = urand.Study(study_name, memory=True)
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

def simulate_assignments_mproc(n_participants, n_simulations, factor_combination_seed, starting_seed, simulation_label,
                               study_name='Test Study', db_name='test.db', nproc=4,
                               fixed_participants=True):
	simulation_data_folder = os.path.join('data', 'simulations', str(simulation_label))
	if os.path.exists(simulation_data_folder) and os.path.isdir(simulation_data_folder):
		shutil.rmtree(simulation_data_folder)
	os.makedirs(simulation_data_folder)

	if fixed_participants:
		study = Study(study_name, memory=True)
		study.starting_seed = starting_seed
		study.generate_dummy_participants(n_participants, factor_combination_seed)
		study.export_history(os.path.join(simulation_data_folder, 'participants.csv'))
		pdf_participants = pd.read_csv(os.path.join(simulation_data_folder, 'participants.csv'),
			                             dtype=object, encoding='utf8')
		pdf_participants = pdf_participants[['id'] + ['f_' + factor for factor in sorted(study.factors.keys())] +
							['user']]
		pdf_participants.to_csv(os.path.join(simulation_data_folder, 'participants.csv'),
		                                                 index=False)

	lst_trial_seed = np.random.default_rng(starting_seed).integers(low=1, high=50000, size=n_simulations)
	lst_factor_combination_seed = np.random.default_rng(factor_combination_seed).integers(low=1, high=50000,
	                                                                                      size=n_simulations)



	lst_paramsets = list(zip(lst_trial_seed,
	                         lst_factor_combination_seed,
	                         list(range(1, n_simulations + 1)),
	                         [n_participants] * n_simulations,
	                         [simulation_data_folder] * n_simulations,
	                         [study_name] * n_simulations,
	                         [fixed_participants]* n_simulations
	                         ))

	mproc_pool = Pool(nproc)
	mproc_pool.starmap(process_isolated_trial, lst_paramsets)
	return 0

def estimate_study_imbalance(simulation_label, study_name='Test Study'):
	simulation_data_folder = os.path.join('data', 'simulations', str(simulation_label))
	lst_trial_files = [fname for fname in glob.glob(os.path.join(simulation_data_folder, "trial_*.csv"))]
	max_participants = pd.read_csv(lst_trial_files[0]).shape[0]
	pdf_stats = pd.DataFrame(columns=['n_participants', 'mean_d', 'min_d', 'trial_fname'])
	for fname in lst_trial_files:
		pdf_trial = pd.read_csv(fname, dtype=object, encoding='utf8')
		study = urand.Study(study_name, memory=True)
		study.starting_seed = pdf_trial['starting_seed'].values[0]
		lst_mean_d = []
		lst_max_d = []
		for n_participants in range(1, max_participants + 1):
			pdf_trial_n = pdf_trial.iloc[:n_participants,]

			study.upload_existing_history(pdf=pdf_trial_n[[col for col in pdf_trial_n.columns if col not in ['trial_no', 'starting_seed']]].iloc[[-1]].copy())
			pdf_urns = study.get_study_urns()
			lst_mean_d.append(pdf_urns['d'].mean())
			lst_max_d.append(pdf_urns['d'].max())
		pdf_trial_stats = pd.DataFrame({'n_participants': list(range(1, max_participants + 1)),
		                                'mean_d': lst_mean_d,
		                                'min_d': lst_max_d
		                                })
		pdf_trial_stats['trial_fname'] = fname
		pdf_stats = pd.concat([pdf_stats, pdf_trial_stats], ignore_index=True).reset_index(drop=True)
	pdf_stats.to_csv(os.path.join(simulation_data_folder, 'study_imbalance.csv'), index=False)
	return pdf_stats


if __name__ == '__main__':
	test_upload_without_seed()
	test_upload_with_seed()
	simulate_assignments(30, 4, 100, 100,
	                     1, fixed_participants=True)
	simulate_assignments_mproc(30, 4, 100, 100, 1, nproc=4, fixed_participants=False)


