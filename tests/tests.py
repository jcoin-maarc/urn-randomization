from urand import Study, db
import os
import pandas as pd


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


if __name__ == '__main__':
	test_upload_without_seed()
	test_upload_with_seed()
