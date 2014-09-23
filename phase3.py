import os
import multiprocessing
import pymworks
import matplotlib.pyplot as plt

def get_animals_and_their_session_filenames(path):
    '''
    Returns a dict with animal names as keys (it gets their names from the
        folder names in 'input' folder--each animal should have its own
        folder with .mwk session files) and a list of .mwk filename strings as
        values.
            e.g. {'V1': ['V1_140501.mwk', 'V1_140502.mwk']}

    :param path: a string of the directory name containing animals' folders
    '''
    #TODO maybe make this better, it's slow as hell and ugly
    result = {}
    dirs_list = [each for each in os.walk(path)]
    for each in dirs_list[1:]:
        files_list = each[2]
        animal_name = each[0].split("/")[len(each[0].split("/")) - 1]
        result[animal_name] = [] #list of filenames
        for filename in files_list:
            if not filename.startswith('.'): #dont want hidden files
                result[animal_name].append(filename)
    return result

def analyze_sessions(animals_and_sessions, graph_summary_stats=False):
    pool = multiprocessing.Pool(None)
    results = []
    for animal, sessions in animals_and_sessions.iteritems():
        result = pool.apply_async(get_data_for_figure,
            args=(animal, sessions))
        results.append(result)
    pool.close()
    pool.join()

    all_data = []
    for each in results:
        data_for_animal = each.get()
        all_data.append(data_for_animal)
        make_a_figure(data_for_animal)

def make_a_figure(data_for_animal):
    plt.close('all')

    f, ax_arr = plt.subplots(2, 1)
    f.suptitle(data_for_animal["animal_name"] + " phase 3 performance (all stimuli 30 deg. visual angle size)")

    ax_arr[0].plot(
        data_for_animal["rotations"],
        data_for_animal["pct_corrects"],
        "-o",
        color="turquoise",
        linewidth=3.0,
    )
    ax_arr[0].set_xlim(-65.0, 65.0)
    ax_arr[0].set_ylim(0.0, 100.0)
    ax_arr[0].grid(axis="y")
    ax_arr[0].set_xlabel("Stimulus rotation in depth (degrees)")
    ax_arr[0].set_ylabel("Percent correct")

    ax_arr[1].plot(
        data_for_animal["rotations"],
        data_for_animal["total_trials"],
        "-o",
        color="tomato",
        linewidth=3.0
    )
    ax_arr[1].set_xlim(-65.0, 65.0)
    ax_arr[1].set_ylim(0, max(data_for_animal["total_trials"]))
    ax_arr[1].set_xlabel("Stimulus rotation in depth (degrees)")
    ax_arr[1].set_ylabel("Sample size (total trials)")

    plt.show()

def get_data_for_figure(animal_name, sessions):
    all_trials = get_trials_from_all_sessions(animal_name, sessions)
    all_size_30 = get_size_30_trial_results(all_trials)
    rotations, pct_corrects, totals = get_stats_for_each_rotation(all_size_30)
    print "Finished analysis for ", animal_name
    return {
        "animal_name": animal_name,
        "rotations": rotations,
        "pct_corrects": pct_corrects,
        "total_trials": totals
    }

def get_stats_for_each_rotation(all_size_30_trials):
    rotations = []
    pct_corrects = []
    total_trials = []
    for rotation, behavior_list in all_size_30_trials.iteritems():
        success = 0
        failure = 0
        ignore = 0
        for behavior in behavior_list:
            if behavior == "success":
                success += 1
            elif behavior == "failure":
                failure += 1
            elif behavior == "ignore":
                ignore += 1
            else:
                print "unknown behavior"
        try:
            pct_correct = ((float(success))/(float(success + failure + ignore))) * 100
            total = success + failure + ignore
            rotations.append(rotation)
            pct_corrects.append(pct_correct)
            total_trials.append(total)
        except ZeroDivisionError:
            pass
    xyz = zip(rotations, pct_corrects, total_trials)
    xyz.sort()
    rotations, pct_corrects, total_trials = zip(*xyz)
    return rotations, pct_corrects, total_trials

def get_size_30_trial_results(all_trials):
    '''
    Returns a dict with stim rotation keys and a list of behavior_outcome
    as values. Returns only size 30 results because only this size can
    rotate in phase 3.
    '''
    result = {}
    for trial in all_trials:
        if trial["stm_size"] == 30.0:
            try:
                result[trial["stm_rotation"]].append(trial["behavior_outcome"])
            except KeyError:
                result[trial["stm_rotation"]] = [trial["behavior_outcome"]]
    return result

def get_trials_from_all_sessions(animal_name, sessions):
    print "Starting analysis for ", animal_name
    all_trials_all_sessions = []
    for session in sessions:
        trials = get_session_trials(animal_name, session)
        all_trials_all_sessions += trials
    return all_trials_all_sessions

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

if __name__ == "__main__":
    animals_and_sessions = get_animals_and_their_session_filenames("input/phase3")
    analyze_sessions(animals_and_sessions)