from urand import Study

study = Study('Example Study')
#study.generate_dummy_participants(1000, 100)
study.export_history('test.csv')
study.print_config()
# participant = study.asgmt(id="80",
#                           user="test",
#                           datetime=
#                           f_institute="10",
#                           f_pretreatment="prior radiotherapy",
#                           f_sex="male",
#                           )
#study.randomize(participant)
#study.upload_history('test.csv')