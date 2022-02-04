from urand import Study, db
import os
import pandas as pd


def test_upload_with_seed(study_name):
    study = Study(study_name, memory=True)
    df_file = pd.read_csv(os.path.join("data", "test_asgmts_with_seed.csv"))
    study.upload_existing_history(
        file=os.path.join("data", "test_asgmts_with_seed.csv")
    )
    df_participants = db.get_participants(study.participant, study.session)
    assert (
        df_participants.shape[0] == df_file.shape[0]
    ), "Uploading file with seed unsuccessful"
    return True


def test_upload_without_seed(study_name):
    study = Study(study_name, memory=True)
    df_file = pd.read_csv(os.path.join("data", "test_asgmts_without_seed.csv"))
    study.upload_existing_history(
        file=os.path.join("data", "test_asgmts_without_seed.csv")
    )
    df_participants = db.get_participants(study.participant, study.session)
    assert (
        df_participants.shape[0] == df_file.shape[0]
    ), "Uploading file without seed unsuccessful"
    return True


if __name__ == "__main__":
    study = Study("CHS JCOIN", memory=False)
    study.generate_dummy_participants(30, 100)
    study.export_history(os.path.join("data", "test_asgmts_with_seed.csv"))
    df = pd.read_csv(os.path.join("data", "test_asgmts_with_seed.csv"), dtype=object)
    del df["bg_state"]
    df.to_csv(os.path.join("data", "test_asgmts_without_seed.csv"), index=False)
    test_upload_without_seed("CHS JCOIN")
    test_upload_with_seed("CHS JCOIN")
