from urand import Study

study = Study('Example Study')
study.print_config()
participant1 = study.participant(id='001',
                                 user='testing',
                                 f_institute='4',
                                 f_pretreatment='no prior treatment',
                                 f_sex='male'
                                )
participant2 = study.participant(id='002',
                                 user='testing',
                                 f_institute='7',
                                 f_pretreatment='prior radiotherapy',
                                 f_sex='female'
                                )
study.randomize(participant1)
study.randomize(participant2)
study.export_history('history.csv')
