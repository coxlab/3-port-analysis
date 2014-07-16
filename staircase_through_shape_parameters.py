import os
import multiprocessing
import datetime
import pymworks
import matplotlib.pyplot as plt

def get_animals_and_their_session_filenames(path):
    '''
    Returns a dict with animal names as keys (it gets their names from the
        folder names in 'input' folder--each animal should have its own
        folder with .mwk session files) and a list of .mwk filename strings as
        values.
            e.g. {'V1': ['V1_140501', 'V1_140502']}

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
    print("Starting analysis for animals:")
    for each in result.keys():
        print(each)
    return result

def analyze_sessions(animals_and_sessions, graph_as_group=False):
    '''
    Starts analysis for each animals' sessions in a new process to use cores.
        We don't want to wait all day for this, y'all.

    :param animals_and_sessions: a dict with animal names as keys and
        a list of their session filenames as values.
    '''
    #use all CPU cores to process data
    pool = multiprocessing.Pool(None)

    results = [] #list of multiprocessing.AsyncResult objects
    for animal, sessions in animals_and_sessions.iteritems():
        result = pool.apply_async(analyze_animal_sessions,
            args=(animal, sessions))
        results.append(result)
    pool.close()
    pool.join() #block until all the data has been processed
    if graph_as_group:
        raise NotImplementedError, "Group graphing coming soon..."
    #
    print("Graphing session data...")
    for each in results:
        data_for_animal = each.get() #returns analyze_animal_sessions result
        make_a_figure(data_for_animal)

    print("Finished")

def make_a_figure(data):
    '''
    Shows a graph of an animal's performance and trial info.

    :param data: a dict with x and y value lists returned by
        analyze_animal_sessions()
    '''

    f, ax_arr = plt.subplots(2, 2) #make 4 subplots for figure
    f.suptitle(data["animal_name"]) #set figure title to animal's name
    f.subplots_adjust(bottom=0.08, hspace=0.4) #fix overlapping labels

    ax_arr[0, 0].plot(data["x_vals"], data["total_pct_correct_y_vals"], "bo")
    ax_arr[0, 0].set_title("% correct - all trials")
    ax_arr[0, 0].axis([0, len(data["x_vals"]), 0.0, 100.0])
    ax_arr[0, 0].set_xlabel("Session number")

    ax_arr[0, 1].plot(data["x_vals"], data["pct_corr_in_center_y_vals"], "bo")
    ax_arr[0, 1].set_title("% correct - trials with stim in center")
    ax_arr[0, 1].axis([0, len(data["x_vals"]), 0.0, 100.0])
    ax_arr[0, 1].set_xlabel("Session number")

    ax_arr[1, 0].plot(data["x_vals"], data["total_trials_y_vals"], "bo")
    ax_arr[1, 0].set_title("Total trials in session")
    ax_arr[1, 0].axis([0, len(data["x_vals"]), 0, \
        max(data["total_trials_y_vals"])])
        #largest y axis tick is largest number of trials in a session
    ax_arr[1, 0].set_xlabel("Session number")

    ax_arr[1, 1].plot(data["x_vals"], data["num_trials_stim_in_center_y_vals"],
        "bo")
    ax_arr[1, 1].set_title("Total trials with stim in center of the screen")
    ax_arr[1, 1].axis([0, len(data["x_vals"]), 0, \
        max(data["total_trials_y_vals"])])
        #largest y axis tick is largest number of trials in a session
        #so it's easier to compare total trials and total trials with
        #stim in center
    ax_arr[1, 1].set_xlabel("Session number")

    plt.show() #show each figure, user can save if he/she wants

    #make plot of the % of trials in center
    plt.close("all")
    plt.plot(data["x_vals"], data["pct_trials_stim_in_center"], "bo")
    plt.axis([0, len(data["x_vals"]), 0.0, 100.0])
    plt.title("% trials with stim in center " + data["animal_name"])
    plt.xlabel("Session number")
    plt.show()

def analyze_animal_sessions(animal_name, sessions):
    '''
    Analyzes one animals' sessions and outputs dict with x and y value lists
    for different types of graphs, e.g. percent correct, total trials, etc.
    See return dict below.
    This is wrapped by analyze_sessions() so it can run in a process on
    each CPU core.

    :param animal_name: name of the animal (string)
    :param sessions: the animal's session filenames (list of strings)
    '''

    list_of_session_stats = get_stats_for_each_session(animal_name, sessions)

    x_vals = [each["session_number"] for each in list_of_session_stats]
    pct_corr_whole_session_y = [each["pct_correct_whole_session"] for each in \
        list_of_session_stats]
    pct_corr_in_center_y = [each["pct_correct_stim_in_center"] for each in \
        list_of_session_stats]
    total_num_trials_y = [each["total_trials"] for each in \
        list_of_session_stats]
    total_trials_stim_in_center_y = [each["trials_with_stim_in_center"] for \
        each in list_of_session_stats]
    pct_trials_stim_in_center = [each["pct_trials_stim_in_center"] for \
        each in list_of_session_stats]

    return {"x_vals": x_vals, #x axis will be session number for all graphs
            "total_pct_correct_y_vals": pct_corr_whole_session_y,
            "pct_corr_in_center_y_vals": pct_corr_in_center_y,
            "total_trials_y_vals": total_num_trials_y,
            "num_trials_stim_in_center_y_vals": total_trials_stim_in_center_y,
            "pct_trials_stim_in_center": pct_trials_stim_in_center,
            "animal_name": animal_name}

def get_stats_for_each_session(animal_name, sessions):
    '''
    Returns a list of dicts with statistics about each session for an
    animal. e.g.
    all_session_results = [{
        'filename': 'AB1_140617.mwk',
        'session_number': 1,
        'ignores': 2,
        'successes': 2,
        'failures': 0,
        'total_trials': 4,
        'd_prime_overall': 1.0,
        'pct_correct_overall': 50.0,
        'pct_failure_overall': 0.0,
        'pct_ignore_overall': 50.0,
        'd_prime_by_size': {
            '40.0': 1.0,
            '35.0': 0.8,
            etc
        },
        'pct_correct_by_size': {
            '40.0': 50.0,
            etc
        },
        'pct_failure_by_size': {
            '40.0': 0.0,
            etc
        }
        ...
        other keys in result:
        'pct_ignore_by_size',
        'total_trials_by_size'

    },

    #Note the NoneType values in this session

    {
        'filename': 'AB1_140618.mwk',
        'session_number': 2,
        'ignores': 0,
        'successes': 0,
        'failures': 0,
        'total_trials': 0,
        'd_prime_overall': None,
        'pct_correct_overall': None,
        'pct_failure_overall': None,
        'pct_ignore_overall': None
        'd_prime_by_size': key: size value: None,
        'pct_correct_by_size': key: size value: None,
        'pct_failure_by_size': key: size value: None
        ...
        other keys in result:
        'pct_ignore_by_size',
        'total_trials_by_size',
    }]

    NOTE: if there are no trials for the denominator of a key
        (e.g. pct_correct or d_prime), the key's value is set to None.
        Behavior outcomes (e.g. ignores, successes, etc.) with no occurances
        are left with value = 0.
    '''
    #TODO break this down into more functions...it's a bit difficult to read
    all_session_results = []
    session_num = 1
    for session in sessions:
        all_trials = get_session_trials(animal_name, session)

        #make dict to store session data
        session_result = {"session_number": session_num,
                          "total_trials": len(all_trials),
                          "filename": session}


        total_trials_by_size = {}
        successes = 0
        failures = 0
        ignores = 0
        #keep track of total successes and failures for each size
        num_failure_by_size = {}
        num_success_by_size = {}
        num_ignores_by_size = {}

        for trial in all_trials:
            #add trial to total trials for each size
            try:
                total_trials_by_size[str(trial["stm_size"])] += 1
            except KeyError:
                total_trials_by_size[str(trial["stm_size"])] = 1

            #track successes and failures for each size, will use for d'
            if trial["behavior_outcome"] == "success":
                successes += 1
                try:
                    num_success_by_size[str(trial["stm_size"])] += 1
                except KeyError:
                    num_success_by_size[str(trial["stm_size"])] = 1

            elif trial["behavior_outcome"] == "failure":
                failures += 1
                try:
                    num_failure_by_size[str(trial["stm_size"])] += 1
                except KeyError:
                    num_failure_by_size[str(trial["stm_size"])] = 1
            elif trial["behavior_outcome"] == "ignore":
                ignores += 1
                try:
                    num_ignores_by_size[str(trial["stm_size"])] += 1
                except KeyError:
                    num_ignores_by_size[str(trial["stm_size"])] = 1
            else:
                #this really shouldnt happen, but just in case...
                print "No behavior_outcome in trial ", trial["trial_num"], \
                    "for animal ", animal_name, " session ", session
                #dont include this trial in total trials
                total_trials_by_size[str(trial["stm_size"])] -= 1

        #done with for loop, now populate data for session_result
        #first add data we already have...
        session_result["successes"] = successes
        session_result["failures"] = failures
        session_result["ignores"] = ignores
        try:
            session_result["d_prime_overall"] = (float(successes)/float(\
                successes + failures)) - (float(failures)/float(\
                successes + failures))
        except ZeroDivisionError:
            session_result["d_prime_overall"] = None
        session_result["total_trials_by_size"] = total_trials_by_size

        #now get ready to add data from by_size dicts...
        d_prime_by_size = {}
        pct_correct_by_size = {}
        pct_failure_by_size = {}
        pct_ignore_by_size = {}

        for stim_size in total_trials_by_size:
            #add any missing size keys with 0 value to make life easier
            num_success_by_size = addMissingKey(num_success_by_size, stim_size)
            num_failure_by_size = addMissingKey(num_failure_by_size, stim_size)
            num_ignores_by_size = addMissingKey(num_ignores_by_size, stim_size)

            try:
                d_prime_by_size[stim_size] = (float(num_success_by_size[\
                    stim_size])/float(num_success_by_size[stim_size] + \
                    num_failure_by_size[stim_size])) - (float(\
                    num_failure_by_size[stim_size])/float(num_success_by_size[\
                    stim_size] + num_failure_by_size[stim_size]))
            except ZeroDivisionError:
                d_prime_by_size[stim_size] = None

            total_trials_for_size = float(num_success_by_size[stim_size] + \
                num_ignores_by_size[stim_size] + num_failure_by_size[stim_size])

            try:
                pct_correct_by_size[stim_size] = (float(num_success_by_size[\
                    stim_size]))/total_trials_for_size
            except ZeroDivisionError:
                pct_correct_by_size[stim_size] = None

            try:
                pct_failure_by_size[stim_size] = (float(num_failure_by_size[\
                    stim_size]))/total_trials_for_size
            except ZeroDivisionError:
                pct_failure_by_size[stim_size] = None

            try:
                pct_ignore_by_size[stim_size] = (float(num_ignores_by_size[\
                    stim_size]))/total_trials_for_size
            except ZeroDivisionError:
                pct_ignore_by_size[stim_size] = None

        #finally, add results to the session's results dict
        session_result["d_prime_by_size"] = d_prime_by_size
        session_result["pct_correct_by_size"] = pct_correct_by_size
        session_result["pct_failure_by_size"] = pct_failure_by_size
        session_result["pct_ignore_by_size"] = pct_ignore_by_size

        all_session_results.append(session_result)
        session_num += 1
    return all_session_results

def addMissingKey(size_dict, key):
    '''
    Helper func so you don't have to check whether a key exists before doing
    math with its values. If a key doesn't exist in one of the by_size dicts,
    addMissingKey will add the key with value 0 and return the dict.
    '''
    if not key in size_dict:
        size_dict[key] = 0
        return size_dict
    return size_dict

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
    path = 'input/' + animal_name + '/' + session_filename

    df = pymworks.open_file(path)
    events = df.get_events(["success", "failure", "ignore", "stm_size"])

    trials = []
    index = 0
    trial_num = 1
    while index < len(events):
        if events[index].name != "stm_size" and events[index].value == 1:
            #only do try statement if event name is success, failure, or ignore
            try:
                if events[index + 1].name == "stm_size":
                    #only enter this try statement if success, failure, or
                    #ignore is followed by a stm_size
                    try:
                        #dont add if there's another stm_size after first
                        #stm_size
                        if events[index + 2].name != "stm_size":
                            trial = {
                                "trial_num": trial_num,
                                "behavior_outcome": events[index].name,
                                "stm_size": events[index + 1].value
                            }
                            trials.append(trial)
                            trial_num += 1
                    except IndexError:
                        #add to results list if final event is a stm_size
                        trial = {
                            "trial_num": trial_num,
                            "behavior_outcome": events[index].name,
                            "stm_size": events[index + 1].value
                        }
                        trials.append(trial)

            except IndexError:
                print "Last event was a behavior_outcome with no size data..."
        index += 1

    return trials

if __name__ == "__main__":
    animals_and_sessions = get_animals_and_their_session_filenames('input')
    analyze_sessions(animals_and_sessions)