from pylsl import resolve_stream, local_clock
import os
import time
from pylsl import StreamOutlet, StreamInfo, StreamInlet, resolve_streams
import mne
import numpy as np
import events
import eeg
import threading
import csv
import numpy as np

samp_freq = 1000

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
    stim_data = np.zeros((1, len(raw.times)))
    info_stim = mne.create_info(['STI 014'], samp_freq, ['stim'])
    stim_raw = mne.io.RawArray(stim_data, info_stim)
    raw.add_channels([stim_raw], force_update_info = True)

    start_time = stats_dict['eeg start'] #- stats_dict['offset']
    for event in event_data:
        event[0] -= start_time
        event[0] = round(event[0] * samp_freq)
        print(event)
    raw.add_events(event_data, 'STI 014', replace = True)
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
    print('first eeg sample: %f'%first_timestamp)
    return raw, eeg_data_path

# push events to trigger inlet
def push_samples(outlet_events, stats_dict):
    for i in range(1,11):
        cur_time = local_clock()
        time.sleep(1)
        print('sample %d offset: %f'%(i, local_clock() - cur_time))
        stats_dict['sample %d pushed'%i] = local_clock()
        outlet_events.push_sample([str(i)], local_clock())
        #outlet_events.push_sample([str(i)], local_clock())
    outlet_events.push_sample(["0"])
    time.sleep(0.00001)
    del outlet_events

# reload the raw and print relevant info
def reload_and_print(eeg_data_path):
    raw = mne.io.read_raw_fif(eeg_data_path, preload = True)
    events = mne.find_events(raw, stim_channel = 'STI 014', shortest_event = 1, initial_event = True)
    #print(raw.n_times)
    #print(raw.info)
    print('surviving events')
    print(events)

if __name__ == '__main__':
    # dict for stats/start times
    stats_dict = {
        'event stream initialized': False,
        'eeg stream initialized': False,
        'too old found' : False
    }

    # getting subject number
    subject_num = input('enter a subject number: ')

    # create outlet for the events
    info_events = StreamInfo('event_stream', 'events', 1, 0, 'string', str(subject_num))
    event_outlet = StreamOutlet(info_events)

    all_streams = resolve_streams()
    for stream in all_streams:
        print("Stream Name: %s"%stream.name())
        print("Stream Type: %s"%stream.type())
        print("Stream Hostname: %s"%stream.hostname())
    # create threads for recording eeg data and event data
    thread_events = threading.Thread(target = events.event_inlet, args = (stats_dict, subject_num))
    thread_eeg = threading.Thread(target = eeg.eeg_inlet, args = (stats_dict, subject_num))

    # start the threads
    thread_events.start()
    thread_eeg.start()

    # push the test samples
    while stats_dict['eeg stream initialized'] == False or stats_dict['event stream initialized'] == False:
        pass
    stats_dict['recording start'] = local_clock()
    #stats_dict['stream init begin'] = local_clock()
    push_samples(event_outlet, stats_dict)

    # wait for the recording threads to finish
    thread_eeg.join()
    thread_events.join()

    # load the events and the raw object
    event_data = load_events()
    raw, eeg_data_path = load_raw()
    print(raw.n_times)

    # add the events to the raw object
    add_raw_events(raw, event_data, stats_dict)

    # reload the raw and print relevant info
    reload_and_print(eeg_data_path)

    # save the timing statistics to a csv
    stats_csv(stats_dict)

    for i in range(1,11):
        if i == 1:
            print('sample %d - sample %d offset: %f'%(i, i - 1, stats_dict['sample %d pushed'%i] - stats_dict['recording start']))
        else:
            print('sample %d - sample %d offset: %f'%(i, i - 1, stats_dict['sample %d pushed'%i] - stats_dict['sample %d pushed'%(i-1)]))
    print('eeg initialization to time of first eeg sample: %f'%(stats_dict['eeg start'] - stats_dict['eeg stream init end']))
    print('eeg initialization to start of recording: %f'%(stats_dict['recording start'] - stats_dict['eeg stream init end']))
    print('start of recording to time of first eeg sample: %f'%(stats_dict['eeg start'] - stats_dict['recording start']))
    print('start of recording to time of first trigger sample: %f'%(stats_dict['sample 1 pushed'] - stats_dict['recording start']))
    print('expected delay: %f'%(1 - (stats_dict['sample 1 pushed'] - stats_dict['eeg start'])))


    ## find EEG stream
    #print('\n\nLooking for EEG stream....\n\n')
    #streams = resolve_stream('type', 'EEG')
    #eeg_stream_name = streams[0].name()
    #print('\n\nFound EEG stream named %s\n\n.'%eeg_stream_name)

        #rec = StreamInlet(info_eeg)
    #rec = StreamRecorder(
    #    record_dir = save_path,
    #    fname = 'mot_%d'%n,
    #    stream_name = eeg_stream_name,
    #    fif_subdir = True
    #    )

    #stats_dict['pre_rec_start'] = local_clock()
    #rec.start()
    #start_time = local_clock()
    #stats_dict['start time recording'] = start_time



        #filename = os.path.join(save_path, 'fif')
    #filename = os.path.join(filename, 'mot_' + str(n) + '-EGI NetAmp 0-raw.fif')
    #raw = mne.io.read_raw_fif(filename, preload = True)
    #print(raw.n_times)
