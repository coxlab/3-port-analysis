import os
import multiprocessing
import math
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
    '''
    Use the multiprocessing module to analyze sessions from multiple animals in
    parallel. Add stats from each animal (a dict, the result of
    get_data_for_figure()) to the all_data list for further processing (i.e.
    get_summary_stats_data()).
    '''
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
        data_for_animal = each.get() #returns result of get_data_for_figure()
        all_data.append(data_for_animal) #need this to stay around for summary statistics
        make_a_figure(data_for_animal) #make a figure with data for this animal

    if graph_summary_stats:
        data = get_summary_stats_data(all_data) #process all animal data
        make_summary_stats_figure(data) #make plots with processed summary stats

def make_summary_stats_figure(data):
    '''
    Plots summary stats data (i.e. mean, standard dev, etc) for all animals.

    @param data: a dict with all our summary stats data, from get_summary_stats_data()
    '''

    plt.close('all')

    f, ax_arr = plt.subplots(2, 1)
    f.suptitle("All animals percent correct (all stimuli 30 degrees visual angle size)")

    ax_arr[0].errorbar(
        data["x_vals_rotations"],
        data["y_vals_pct_correct"],
        yerr=data["std_devs"],
        fmt="-o",
        color="turquoise",
        linewidth=3.0
    )
    ax_arr[0].set_xlim(-65.0, 65.0)
    ax_arr[0].set_ylim(0.0, 100.0)
    ax_arr[0].grid(axis="y")
    ax_arr[0].set_ylabel("Percent correct +/- SSD")
    ax_arr[0].errorbar(
        [0.0],
        [data["size_40_data"]["size_40_avg"]],
        yerr=[data["size_40_data"]["size_40_std_dev"]],
        fmt="*",
        color="violet",
        markersize=9.0
    )
    ax_arr[0].annotate(
        "stimulus size = 40; rotation = 0",
        xy=(0, data["size_40_data"]["size_40_avg"]),
        xycoords="data",
        textcoords="offset points",
        xytext=(30, -85),
        ha="center",
        va="top",
        arrowprops=dict(facecolor="black", shrink=0.1, width=1, headwidth=3.0)
    )

    ax_arr[1].errorbar(
        data["sample_size_data"]["x_vals_rotations"],
        data["sample_size_data"]["y_vals_num_trials"],
        yerr=data["sample_size_data"]["std_devs_num_trials"],
        fmt="-o",
        color="tomato",
        linewidth=3.0
    )
    ax_arr[1].set_xlim(-65.0, 65.0)
    ax_arr[1].set_ylim(0, max(data["sample_size_data"]["y_vals_num_trials"]) + max(data["sample_size_data"]["std_devs_num_trials"]))
    ax_arr[1].set_ylabel("Sample size (total trials) +/- SSD")
    ax_arr[1].set_xlabel("Stimulus rotation in depth (degrees)")

    plt.show()

    std_errors_performance = [sd/math.sqrt(len(data["std_devs"])) for sd in data["std_devs"]]
    std_errors_samplesize = [sd/math.sqrt(len(data["sample_size_data"]["std_devs_num_trials"])) for sd in data["sample_size_data"]["std_devs_num_trials"]]
    max_performance = [mean + std_error for mean, std_error in zip(data["y_vals_pct_correct"], std_errors_performance)]
    min_performance = [mean - std_error for mean, std_error in zip(data["y_vals_pct_correct"], std_errors_performance)]
    max_samplesize = [mean + std_error for mean, std_error in zip(data["sample_size_data"]["y_vals_num_trials"], std_errors_samplesize)]
    min_samplesize = [mean - std_error for mean, std_error in zip(data["sample_size_data"]["y_vals_num_trials"], std_errors_samplesize)]

    plt.close('all')

    f, ax_arr = plt.subplots(2, 1)
    f.suptitle("All animals percent correct (all stimuli 30 degrees visual angle size)")

    ax_arr[0].plot(
        data["x_vals_rotations"],
        data["y_vals_pct_correct"],
        color="turquoise",
        linewidth=1.5
    )
    ax_arr[0].fill_between(
        data["x_vals_rotations"],
        max_performance,
        min_performance,
        color="none",
        facecolor="turquoise",
        alpha=0.3
    )
    ax_arr[0].errorbar(
        [0.0],
        [data["size_40_data"]["size_40_avg"]],
        yerr=[data["size_40_data"]["size_40_std_error"]],
        fmt="*",
        color="violet",
        markersize=7.0
    )
    ax_arr[0].annotate(
        "stimulus size = 40; rotation = 0",
        xy=(0, data["size_40_data"]["size_40_avg"]),
        xycoords="data",
        textcoords="offset points",
        xytext=(30, -85),
        ha="center",
        va="top",
        arrowprops=dict(facecolor="black", shrink=0.12, width=1, headwidth=3.0)
    )
    ax_arr[0].set_xlim(-65.0, 65.0)
    ax_arr[0].set_ylim(0.0, 100.0)
    ax_arr[0].set_ylabel("Percent correct +/- SEM")
    ax_arr[0].grid(axis="y")

    ax_arr[1].plot(
        data["sample_size_data"]["x_vals_rotations"],
        data["sample_size_data"]["y_vals_num_trials"],
        color="tomato",
        linewidth=1.5
    )
    ax_arr[1].fill_between(
        data["sample_size_data"]["x_vals_rotations"],
        max_samplesize,
        min_samplesize,
        color="none",
        facecolor="tomato",
        alpha=0.3
    )
    ax_arr[1].set_xlim(-65.0, 65.0)
    ax_arr[1].set_ylim(0.0, max(max_samplesize))
    ax_arr[1].set_ylabel("Sample size (total trials) +/- SEM")
    ax_arr[1].set_xlabel("Stimulus rotation in depth (degrees)")

    plt.show()
    plt.close('all')

    plt.plot(
        data["nth_time_seen_data"]["nth_time_seen"],
        data["nth_time_seen_data"]["nth_performance"],
        color="turquoise",
        linewidth=1.5
    )
    plt.fill_between(
        data["nth_time_seen_data"]["nth_time_seen"],
        [mean + err for mean, err in zip(data["nth_time_seen_data"]["nth_performance"], data["nth_time_seen_data"]["nth_std_errs"])],
        [mean - err for mean, err in zip(data["nth_time_seen_data"]["nth_performance"], data["nth_time_seen_data"]["nth_std_errs"])],
        color="none",
        facecolor="turquoise",
        alpha=0.3
    )
    plt.xlim(1, len(data["nth_time_seen_data"]["nth_time_seen"]))
    plt.ylim(0.0, 100.0)
    plt.grid(axis="y")
    plt.ylabel("Performance (% correct)")

    plt.show()

def get_summary_stats_data(all_data):
    '''
    Returns a dict with summary statistics for all animals.

    @param all_data: a list of dicts where each dict is one animal's performance data;
        each dict is the return value from get_data_for_figure()
    '''
    result1 = {} #keys=rotation_float vals=list of percentage floats for each animal
    result2 = {} #keys=rotation_float vals=list of num_trials ints for each animal
    for animal_data in all_data:
        x = animal_data["rotations"]
        y1 = animal_data["pct_corrects"]
        y2 = animal_data["total_trials"]
        for rotation, pct, sample_size in zip(x, y1, y2):
            try:
                result1[rotation].append(pct)
            except KeyError:
                result1[rotation] = [pct]
            try:
                result2[rotation].append(sample_size)
            except KeyError:
                result2[rotation] = [sample_size]

    #longest list has all animals
    #only want to plot summary stats for datapoints with all animals
    longest_1 = get_longest_vals_list_in_dict(result1)
    x_vals1 = []
    y_vals1 = []
    errors1 = []
    for rotation, percentages in result1.iteritems():
        if len(percentages) == longest_1: # <-- only add results with data for all animals
            mean, std_dev = calc_summary_stats(percentages)
            x_vals1.append(rotation)
            y_vals1.append(mean)
            errors1.append(std_dev)
    xyz1 = zip(x_vals1, y_vals1, errors1)
    xyz1.sort()
    x_vals1, y_vals1, errors1 = zip(*xyz1)


    longest_2 = get_longest_vals_list_in_dict(result2)
    x_vals2 = []
    y_vals2 = []
    errors2 = []
    for rotation, sample_sizes in result2.iteritems():
        if len(sample_sizes) == longest_2:
            mean, std_dev = calc_summary_stats(sample_sizes)
            x_vals2.append(rotation)
            y_vals2.append(mean)
            errors2.append(std_dev)
    xyz2 = zip(x_vals2, y_vals2, errors2)
    xyz2.sort()
    x_vals2, y_vals2, errors2 = zip(*xyz2)

    size_40_pct_corrects = []
    for animal_data in all_data:
        size_40_pct_corrects.append(animal_data["size_40_pct_correct"])

    size_40_mean_pct_correct, size_40_std_dev = calc_summary_stats(size_40_pct_corrects)

    #nth time seen functions arent finished, but this should work when/if they are
    nth_performances = []
    for animal_data in all_data:
        nth_performances.append(animal_data["nth_time_seen_data"]["nth_performance"])
    nth_performances = zip(*nth_performances)

    num_times_seen = []
    performances = []
    nth_std_devs = []
    nth_std_errs = []
    for index, performance in enumerate(nth_performances):
        mean, std_dev = calc_summary_stats(performance)
        num_times_seen.append(index + 1)
        performances.append(mean)
        nth_std_devs.append(std_dev)
        nth_std_errs.append(std_dev/math.sqrt(len(performance)))

    return {
        "x_vals_rotations": x_vals1,
        "y_vals_pct_correct": y_vals1,
        "std_devs": errors1,
        "sample_size_data": {
            "x_vals_rotations": x_vals2,
            "y_vals_num_trials": y_vals2,
            "std_devs_num_trials": errors2
        },
        "size_40_data": {
            "size_40_avg": size_40_mean_pct_correct,
            "size_40_std_dev": size_40_std_dev,
            "size_40_std_error": size_40_std_dev/math.sqrt(len(size_40_pct_corrects))
        },
        "nth_time_seen_data": {
            "nth_time_seen": num_times_seen,
            "nth_performance": performances,
            "nth_std_devs": nth_std_devs,
            "nth_std_errs": nth_std_errs
        }
    }

def get_longest_vals_list_in_dict(dict_with_list_as_values):
    longest = 0
    for k, v in dict_with_list_as_values.iteritems():
        length = len(v)
        if length > longest:
            longest = length
    return longest

def calc_summary_stats(list_of_floats):
    mean = math.fsum(list_of_floats)/len(list_of_floats)
    variance = (math.fsum([(fl - mean)**2.0 for fl in list_of_floats]))/(len(list_of_floats) - 1)
    std_dev = math.sqrt(variance)
    return mean, std_dev

def make_a_figure(data_for_animal):
    '''
    Makes graphs with data from each INDIVIDUAL animal. data_for_animal is a dict--
    the result from get_data_for_figure()--see that documentation for more info
    '''
    plt.close('all')

    #this looks long and complicated, but it's basically just making
    #a plot over and over again with different data
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
    ax_arr[0].set_ylabel("Percent correct")
    ax_arr[0].plot(
        [0.0],
        [data_for_animal["size_40_pct_correct"]],
        "*",
        color="violet",
        markersize=9.0
    )
    ax_arr[0].annotate(
        "stimulus size = 40; rotation = 0; n = %s" % data_for_animal["size_40_total_trials"],
        xy=(0, data_for_animal["size_40_pct_correct"]),
        xycoords="data",
        textcoords="offset points",
        xytext=(30, -85),
        ha="center",
        va="top",
        arrowprops=dict(facecolor="black", shrink=0.12, width=1, headwidth=3.0)
    )

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
    plt.close('all')

    plt.fill_between(
        [index + 1 for index, data in enumerate(data_for_animal["progress_graph_data"]["x"])],
        data_for_animal["progress_graph_data"]["y1"],
        data_for_animal["progress_graph_data"]["y2"],
        facecolor="tomato",
        alpha=0.6
    )

    plt.ylim(-65.0, 65.0)
    plt.xlim(1, max([index + 1 for index, data in enumerate(data_for_animal["progress_graph_data"]["x"])]))
    plt.xticks([index + 1 for index, data in enumerate(data_for_animal["progress_graph_data"]["x"])])
    plt.grid(axis="y")
    plt.xlabel("Bin number (50 trials per bin)")
    plt.ylabel("Range of rotations tested")
    plt.title(data_for_animal["animal_name"] + " rotation progress over time")

    plt.show()
    plt.close('all')

    plt.plot(
        data_for_animal["nth_time_seen_data"]["nth_time_seen"],
        data_for_animal["nth_time_seen_data"]["nth_performance"],
        "-o",
        color="turquoise",
        linewidth=3.0
    )
    plt.title(data_for_animal["animal_name"] + " phase 3 performance by rotation novelty")
    plt.xlim(0, max(data_for_animal["nth_time_seen_data"]["nth_time_seen"]) + 1)
    plt.ylim(0.0, 100.0)
    plt.grid(axis="y")
    plt.xlabel("nth time seen")
    plt.ylabel("Performance (% correct)")

    plt.show()

def get_data_for_figure(animal_name, sessions):
    '''
    Returns a dict with data for one animal.

    @param animal_name: a string
    @param sessions: a list of filename strings
    '''
    all_trials = get_trials_from_all_sessions(animal_name, sessions) #list of trial dicts
    all_size_30 = get_size_30_trial_results(all_trials) #list of all trial dicts where stm_size was 30.0
    rotations, pct_corrects, totals = get_stats_for_each_rotation(all_size_30) #returns 3 lists with rotation floats, performance floats, and sample size ints
    progress_data = get_progress_over_time(all_trials) #returns a dict with data about the range of rotations tested over time
    all_size_40 = get_size_40_outcomes(all_trials) ##list of all trial dicts where stm_size was 40.0
    pct_correct_40 = get_pct_correct_at_size_40(all_size_40) #returns a float for percent correct at size 40.0
    nth_time_seen, nth_performance = get_performance_by_nth_time_seen(all_trials) #not finished, basically ignore this

    print "Finished analysis for ", animal_name
    return {
        "animal_name": animal_name,
        "rotations": rotations,
        "pct_corrects": pct_corrects,
        "total_trials": totals,
        "progress_graph_data": progress_data,
        "size_40_pct_correct": pct_correct_40,
        "size_40_total_trials": len(all_size_40),
        "nth_time_seen_data": {
            "nth_time_seen": nth_time_seen,
            "nth_performance": nth_performance
        }
    }

def get_performance_by_nth_time_seen(all_trials):
    '''
    Not finished, but the idea is to get performance in all rotations (y axis)
    as a function of the number of times each rotation has been presented (x axis).
    See Zoccolan 2009 Fig. 3B to get the idea.
    '''
    tmp = {} #keys=rotation float values=list of behavior_outcome events in order of appearance
    for trial in all_trials:
        if trial["stm_size"] == 30.0:
            try:
                tmp[trial["stm_rotation"]].append(trial["behavior_outcome"])
            except KeyError:
                tmp[trial["stm_rotation"]] = [trial["behavior_outcome"]]
    nth_outcomes = []
    for rotation, outcomes in tmp.iteritems():
        nth_outcomes.append(outcomes)
    nth_outcomes = zip(*nth_outcomes)

    nth_time_seen = []
    nth_performance = []
    for index, outcome_list in enumerate(nth_outcomes):
        success = 0
        failure = 0
        ignore = 0
        for outcome in outcome_list:
            if outcome == "success":
                success += 1
            elif outcome == "failure":
                failure += 1
            elif outcome == "ignore":
                ignore += 1
            else:
                print "get_performance_by_nth_time_seen() FAIL"
        try:
            pct = ((float(success))/(float(success + failure + ignore))) * 100
        except ZeroDivisionError:
            pct = None
        nth_time_seen.append(index + 1)
        nth_performance.append(pct)
    return nth_time_seen, nth_performance

def get_size_40_outcomes(all_trials):
    result = []
    for trial in all_trials:
        if trial["stm_size"] == 40.0:
            result.append(trial["behavior_outcome"])
    return result

def get_pct_correct_at_size_40(behavior_outcome_list):
    '''
    Use this to get performance for size 40 (default) stimuli during presentation
    of stimuli in the "cross."

    @param behavior_outcome_list: a list of dicts where the dicts look like those from
        get_session_trials()
    '''
    success = 0
    failure = 0
    ignore = 0
    for behavior in behavior_outcome_list:
        if behavior == "success":
            success += 1
        elif behavior == "failure":
            failure += 1
        elif behavior == "ignore":
            ignore += 1
        else:
            print "something's wrong, yo. check out get_pct_correct_at_size_40()"

    total_trials = success + failure + ignore
    try:
        pct_correct = ((float(success))/(float(total_trials))) * 100
    except ZeroDivisionError:
        pct_correct = None
        print "Need to write exception code to handle 0 40 deg visual angle trials"
    return pct_correct

def get_progress_over_time(all_trials, trials_per_bin=50):
    '''
    Makes it easy to visualize rotation progress for each animal. Use this to
    decide when to switch rotation in depth direction (i.e. change direction when the
    animal reaches max rotation to the right or left).

    @param all_trials: a list of dicts where the dicts look like those from get_session_trials()
    '''
    num_trials_range = []
    max_rotation_right_in_range = []
    max_rotation_left_in_range = []

    num_trials = trials_per_bin
    tmp_trials_list = []
    for trial in all_trials:
        if trial["stm_size"] == 30.0:
            if len(tmp_trials_list) == trials_per_bin:
                rots = [t["stm_rotation"] for t in tmp_trials_list]
                max_right = max(rots)
                max_left = min(rots)

                num_trials_range.append(num_trials)
                max_rotation_right_in_range.append(max_right)
                max_rotation_left_in_range.append(max_left)

                tmp_trials_list = [trial]
                num_trials += trials_per_bin
            else:
                tmp_trials_list.append(trial)

    return {
        "x": num_trials_range,
        "y1": max_rotation_left_in_range,
        "y2": max_rotation_right_in_range
    }


def get_stats_for_each_rotation(all_size_30_trials):
    '''
    Returns 3 lists. A list of rotations, a list of performance at those rotations,
    and a list of the sample size at those rotations.

    @param all_size_30_trials: a list of trial dicts (trials dicts look like the ones
        in the documentation for get_session_trials())
    '''
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
           "stm_rotation": 0.0
           },
          {"trial_num": 2,
           "behavior_outcome": "success",
           "stm_size": 30.0,
           "stm_rotation": 15.0
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
    analyze_sessions(animals_and_sessions, graph_summary_stats=True)