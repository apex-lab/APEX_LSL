# Written by David Falk (UChicago APEX Lab) to collect data from MOT task.
# This file starts the eeg and event threads. Once those threads collect
# their data it takes the existing MNE Raw object (created in eeg.py) with 
# the EEG and DIN data and adds the events (from events.py) to that object
import os
import mne
import numpy as np
import events
import eeg
import threading

sfreq = 8000 # sampling frequency

# adds events to the raw file and save the raw
def add_raw_events(raw, event_data, stats_dict, eeg_data_path):
    start_time = stats_dict['eeg start']
    for event in event_data:
        event[0] -= start_time
        event[0] = round(event[0] * sfreq)
    raw.add_events(event_data, 'STI 014')
    raw.save(eeg_data_path, overwrite = True)

# load events from the saved event file
def load_events(event_data_path):
    cur_path = os.path.dirname(__file__)
    event_data = np.load(event_data_path)
    return event_data

# load saved mne/eeg raw object
def load_raw(eeg_data_path):
    raw = mne.io.read_raw_fif(eeg_data_path, preload = True)
    return raw

if __name__ == '__main__':
    
    # getting subject number
    subject_num = input('enter a subject/user number: ')
    
    # creating file paths
    cur_path = os.path.dirname(__file__)
    
    # eeg data path
    eeg_data_folder = os.path.join(cur_path, 'raw_data')
    eeg_data_path = os.path.join(eeg_data_folder, subject_num + '_raw.fif')
    
    # events data path
    event_data_folder = os.path.join(cur_path, 'event_data')
    event_data_path = os.path.join(event_data_folder, subject_num + '.npy')
    
    # dict for stats/start times
    stats_dict = {
        'event stream initialized': False,
        'eeg stream initialized': False,
    }

    # create threads for recording eeg data and event data
    thread_events = threading.Thread(target = events.event_inlet, args = (stats_dict, subject_num))
    thread_eeg = threading.Thread(target = eeg.eeg_inlet, args = (stats_dict, subject_num))

    # start the threads
    thread_events.start()
    thread_eeg.start()

    # wait for both streams to be found before collecting data
    while stats_dict['eeg stream initialized'] == False or stats_dict['event stream initialized'] == False:
        pass

    # wait for the recording threads to finish
    thread_eeg.join()
    thread_events.join()

    # load the events and the raw object
    event_data = load_events(event_data_path)
    raw = load_raw(eeg_data_path)

    # add the events to the raw object
    add_raw_events(raw, event_data, stats_dict, eeg_data_path)

    # reload and print events to check if everything worked
    raw, eeg_data_path = load_raw()
    events = mne.find_events(raw)
    for event in events:
        print(event)