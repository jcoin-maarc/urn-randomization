from urand import Study, Participant

study = Study('Example Study')
study.generate_dummy_participants(30, 100)
study.print_config()
participant = Participant(id="56",
                          user="test",
                          f_institute="10",
                          f_pretreatment="prior radiotherapy",
                          f_sex="male",
                          )
study.randomize(participant)
#study.upload_history('test.csv')