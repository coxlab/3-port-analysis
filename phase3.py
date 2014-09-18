import pymworks

def get_session_trials(animal_name, session_filename):
    '''
    Returns a time-ordered list of dicts, where each dict is info about a trial.
    e.g. [{"trial_num": 1,
           "behavior_outcome": "failure",
           "stm_size": 40.0,
           },
          {"trial_num": 2,
           "behavior_outcome": "success",
           "stm_size": 35.0
           }]

    :param animal_name: name of the animal string
    :param session_filename: filename for the session (string)
    '''

    #TODO: unfuck this: hard coded paths not ideal for code reuse
    path = 'input/' + 'phase3/' + animal_name + '/' + session_filename

    df = pymworks.open_file(path)
    events = df.get_events([
        "Announce_TrialStart",
        "Announce_TrialEnd",
        "success",
        "failure",
        "ignore",
        "stm_size",
        "stm_rotation_in_depth"]
    )

    trials = []
    trial_num = 1
    for index, event in enumerate(events):
        if (event.name == "Announce_TrialStart" and
        event.value == 1):
            trial = {
                "trial_num": trial_num,
                "stm_size": None,
                "behavior_outcome": None,
                "stm_rotation": None
            }

            try:
                if events[index - 1].name == "stm_size":
                    trial["stm_size"] = events[index - 1].value
            except IndexError:
                print "stm_size out of range for session", session_filename, \
                index
            try:
                if events[index - 1].name == "stm_rotation_in_depth":
                    trial["stm_rotation"] = float(events[index - 1].value)
            except IndexError:
                print "stm_rotation_in_depth out of range for session", session_filename, index
            try:
                if events[index - 2].name == "stm_size":
                    trial["stm_size"] = events[index - 2].value
            except IndexError:
                print "stm_size out of range for session", session_filename, index
            try:
                if events[index - 2].name == "stm_rotation_in_depth":
                    trial["stm_rotation"] = float(events[index - 2].value)
            except IndexError:
                print "stm_rotation_in_depth out of range for session", session_filename, index
            try:
                if events[index + 1].name in ["success", "failure", "ignore"]:
                    trial["behavior_outcome"] = events[index + 1].name
            except IndexError:
                print "beh_outcome out of range for session", session_filename,\
                 index
            if (trial["stm_size"] is not None and
            trial["behavior_outcome"] is not None and
            trial["stm_rotation"] is not None):
                trials.append(trial)
                trial_num += 1
    return trials