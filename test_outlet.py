from pylsl import StreamOutlet, StreamInlet, StreamInfo, resolve_stream, local_clock
import os
import time
import mne
import numpy as np
import events
import eeg
import threading
import csv
import numpy as np

sfreq = 8000

# timing statistics
def stats_csv(stats_dict):
    save_path = os.getcwd()
    name = os.path.join(save_path, 'stats.csv')
    header = []
    values = []
    for key, value in stats_dict.items():
        header.append(key)
        values.append(value)
    final = zip(header, values)

    with open(name, 'w', newline= '') as f:
        writer = csv.writer(f)
        for pair in final:
            writer.writerow([pair[0], pair[1]])
        f.close()

# adds events to the raw file and save the raw
def add_raw_events(raw, event_data, stats_dict):
    start_time = stats_dict['eeg start']
    for event in event_data:
        event[0] -= start_time
        event[0] = round(event[0] * sfreq)
    raw.add_events(event_data, 'STI 014')
    raw.save(eeg_data_path, overwrite = True)


# load events from the saved event file
def load_events():
    cur_path = os.path.dirname(__file__)
    event_data_folder = os.path.join(cur_path, 'event_data')
    event_data_path = os.path.join(event_data_folder, subject_num + '.npy')
    event_data = np.load(event_data_path)
    return event_data

# load saved mne/eeg raw object
def load_raw():
    cur_path = os.path.dirname(__file__)
    eeg_data_folder = os.path.join(cur_path, 'raw_data')
    eeg_data_path = os.path.join(eeg_data_folder, subject_num + '_raw.fif')
    raw = mne.io.read_raw_fif(eeg_data_path, preload = True)
    time_array = raw.times
    first_timestamp = time_array[0]
    return raw, eeg_data_path

# push events to trigger inlet
def push_samples(outlet_events):
    for i in range(2,11):
        time.sleep(1)
        outlet_events.push_sample([str(i)], local_clock())
    outlet_events.push_sample(["0"])
    time.sleep(0.00001)
    del outlet_events

# reload the raw and print relevant info
def reload_and_print(eeg_data_path):
    raw = mne.io.read_raw_fif(eeg_data_path, preload = True)
    events = mne.find_events(raw, stim_channel = 'STI 014', shortest_event = 1, initial_event = True)

if __name__ == '__main__':
    # dict for stats/start times
    stats_dict = {
        'event stream initialized': False,
        'eeg stream initialized': False
    }

    # getting subject number
    subject_num = input('enter a subject number: ')

    # create outlet for the events
    info_events = StreamInfo('event_stream', 'events', 1, 0, 'string', str(subject_num))
    event_outlet = StreamOutlet(info_events)

    # create threads for recording eeg data and event data
    thread_events = threading.Thread(target = events.event_inlet, args = (stats_dict, subject_num))
    #thread_eeg = threading.Thread(target = eeg.eeg_inlet, args = (stats_dict, subject_num))

    # start the threads
    thread_events.start()
    #thread_eeg.start()

    # push the test samples
    #while stats_dict['eeg stream initialized'] == False or stats_dict['event stream initialized'] == False:
    #    pass
    while stats_dict['event stream initialized'] == False:
        pass

    push_samples(event_outlet)

    # wait for the recording threads to finish
    #thread_eeg.join()
    thread_events.join()

    # load the events and the raw object
    event_data = load_events()
    raw, eeg_data_path = load_raw()

    # add the events to the raw object
    add_raw_events(raw, event_data, stats_dict)

    # reload the raw and print relevant info
    reload_and_print(eeg_data_path)

    # save the timing statistics to a csv
    stats_csv(stats_dict)
