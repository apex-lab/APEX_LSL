from pylsl import resolve_stream, local_clock
import os
from pylsl import StreamInfo, StreamInlet
import mne
import numpy as np
import time

sfreq = 1000

# saves data to the raw_data folder as mne raw object
def save_data(samples, subject_num):

    # preparing the save paths
    rel_path = os.path.dirname(__file__)
    save_folder_path = os.path.join(rel_path, 'raw_data')
    filename = subject_num + '_raw.fif'
    full_save_path = os.path.join(save_folder_path, filename)

    # create the save path if it does not exist
    if not os.path.exists(save_folder_path):
        os.mkdir(save_folder_path)

    # prepare mne file info and creating mne info object
    n_channels = 129
    ch_names = ['E' + str(i) for i in range(1,130)]
    ch_types = ['eeg'] * n_channels
    mne_info = mne.create_info(ch_names = ch_names, sfreq = sfreq, ch_types = ch_types)

    # convert to numpy arrays
    samples_array = np.array(samples).T

    # create raw object
    raw = mne.io.RawArray(samples_array, mne_info)

    # save raw object
    raw.save(full_save_path, overwrite = True)

# pull chunks of data from eeg outlet and save in "samples" array
def pull_chunks(inlet_eeg, stats_dict):
    samples = []
    timestamps = []
    i = 0
    stats_dict['cur time'] = local_clock()
    while True:
        too_old = False
        try:
            start_pull_chunk = local_clock()
            new_samples, new_timestamps = inlet_eeg.pull_chunk()
            stop_pull_chunk = local_clock()
            #if i < 10:
                #print('time to pull chunk: %f'%(stop_pull_chunk - start_pull_chunk))
            i+=1
            if len(new_samples) == 0 or len(new_samples[0]) != 129:
                continue
                #stats_dict['eeg start'] = local_clock()
            #print('length of new samples: %d'%len(new_samples))
            #print('time differential of new samples: %f'%(new_timestamps[-1] - new_timestamps[0]))
            for timestamp in new_timestamps:
                if timestamp < stats_dict['cur time']:
                    too_old = True
                timestamps.append(timestamp)
            if too_old == True:
                stats_dict['too old found'] = True
                continue
            if len(samples) == 0:
                #print('\n\n\nlength of first samples: %f \n\n\n' %len(new_samples))
                stats_dict['eeg start'] = float(new_timestamps[0])
                #stats_dict['cur time'] = local_clock()
                #print('\n\nfirst timestamp: %f \n\n'%new_timestamps[-1])
            for sample in new_samples:
                samples.append(sample)
        except Exception as e:
            stats_dict['eeg stop'] = timestamps[-1]
            stats_dict['eeg runtime'] = stats_dict['eeg stop'] - stats_dict['eeg start']
            del inlet_eeg
            print(e)
            break
    samples_copy = samples.copy()
    del samples
    stats_dict['offset'] = stats_dict['cur time'] - stats_dict['eeg start']
    print('computer times offset: %f'%(stats_dict['eeg start'] - stats_dict['cur time']))
    return samples_copy

# find streams, collect samples, save data
def eeg_inlet(stats_dict, subject_num):

    # find eeg stream
    print('\n\nLooking for EEG stream....\n\n')
    eeg_streams = resolve_stream('type', 'EEG')
    eeg_stream_name = eeg_streams[0].name()
    print('\n\nFound EEG stream named %s\n\n.'%eeg_stream_name)

    stats_dict['eeg stream init begin'] = local_clock()
    inlet_eeg = StreamInlet(eeg_streams[0], recover= False)
    stats_dict['eeg stream init end'] = float(local_clock())
    stats_dict['eeg stream initialized'] = True
    # create the eeg inlet
    while stats_dict['event stream initialized'] == False:
        pass
    stats_dict['eeg stream initialization time'] = stats_dict['eeg stream init end'] - stats_dict['eeg stream init begin']
    #print('initialized inlet')



    # collect our data
    samples_copy = pull_chunks(inlet_eeg, stats_dict)

    # save the data as mne raw object
    save_data(samples_copy, subject_num)
