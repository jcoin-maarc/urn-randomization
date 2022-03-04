from datetime import datetime
import pytz
import pandas as pd

service = "tues_asgmt"
tzone = pytz.timezone("America/Chicago")


def randomize(study, participant):
    if study.study_name == "CHS JCOIN HUB":
        if datetime.now(tzone).weekday() == 1:
            if participant.trt == "MART":
                pdf_assignments = study.export_history()
                pdf_assignments = pdf_assignments.assign(
                    datetime=pd.to_datetime(
                        pdf_assignments["datetime"].astype(str), errors="coerce"
                    )
                    .dt.tz_localize("utc")
                    .dt.tz_convert(tzone)
                )
                pdf_assignments = pdf_assignments.loc[
                    (pdf_assignments["datetime"].dt.date == datetime.now(tzone).date())
                    & (pdf_assignments["trt"] == "MART")
                ]
                if pdf_assignments.shape[0] >= 3:
                    participant.trt = "RMC-Q"
                    participant.user = service
    return participant
