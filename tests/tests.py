from urand import Study, db
import os
import pandas as pd
import pickle
import shutil

def truncate_history_after_tests(session, participant_tbl):
	try:
		num_rows_deleted = session.query(participant_tbl).delete()
		session.commit()
	except:
		session.rollback()
		print("History table not truncated after tests")

def test_upload_with_seed():
	study = Study('Test Study')
	df_file = pd.read_csv(os.path.join('data', 'test_asgmts_with_seed.csv'))
	study.upload_existing_history(os.path.join('data', 'test_asgmts_with_seed.csv'))
	df_participants = db.fetch_participants(study.participant, study.session)
	assert df_participants.shape[0] == df_file.shape[0], "Uploading file with seed unsuccessful"
	truncate_history_after_tests(study.session, study.participant)
	return True

def test_upload_without_seed():
	study = Study('Test Study')
	df_file = pd.read_csv(os.path.join('data', 'test_asgmts_without_seed.csv'))
	study.upload_existing_history(os.path.join('data', 'test_asgmts_without_seed.csv'))
	df_participants = db.fetch_participants(study.participant, study.session)
	assert df_participants.shape[0] == df_file.shape[0], "Uploading file without seed unsuccessful"
	truncate_history_after_tests(study.session, study.participant)
	return True

def simulate_assignments(n_participants, n_simulations, factor_combination_seed, starting_seed, simulation_id):
	simulation_data_folder = os.path.join('data', 'simulations', str(simulation_id))
	if os.path.exists(simulation_data_folder) and os.path.isdir(simulation_data_folder):
		shutil.rmtree(simulation_data_folder)
	os.mkdir(simulation_data_folder)
	study = Study('Test Study')
	study.starting_seed = starting_seed
	study.generate_dummy_participants(n_participants, factor_combination_seed)
	study.export_history(os.path.join(simulation_data_folder, 'participants.csv'))
	pdf_participants = pd.read_csv(os.path.join(simulation_data_folder, 'participants.csv'),
		                             dtype=object, encoding='utf8')
	pdf_participants = pdf_participants[['id'] + ['f_' + factor for factor in sorted(study.factors.keys())] +
						['user']]
	pdf_participants.to_csv(os.path.join(simulation_data_folder, 'participants.csv'),
	                                                 index=False)
	truncate_history_after_tests(study.session, study.participant)
	for trial in range(n_simulations):
		study = Study('Test Study')
		study.starting_seed = starting_seed
		study.upload_new_participants(pdf=pdf_participants)
		study.export_history(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial)))
		pdf_trial_data = pd.read_csv(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial)),
		                             dtype=object, encoding='utf8')
		pdf_trial_data['trial_no'] = trial
		pdf_trial_data['starting_seed'] = starting_seed
		pdf_trial_data.to_csv(os.path.join(simulation_data_folder, 'trial_{0}.csv'.format(trial)))
		nprandom = pickle.loads(study.get_seed())
		starting_seed = nprandom.randint(low=1, high=n_simulations+1, size=1)[0]
		truncate_history_after_tests(study.session, study.participant)


test_upload_with_seed()
test_upload_without_seed()
simulate_assignments(30, 4, 100, 100, 1)

