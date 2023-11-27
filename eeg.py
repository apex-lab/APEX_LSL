# Written by David Falk (UChicago APEX Lab) to collect data from MOT task.
# This file collects and stores the eeg/DIN data in an h5 file in the
# "h5_data" folder. After the recording is finished it collects this h5_data
# from the file and turn this data into an mne Raw object with the DINs stored
# as events.
from pylsl import StreamInlet, resolve_stream
import os
import mne
import numpy as np
import h5py

sfreq = 8000 # sampling frequency for netstation device
din_off_value = 65535 # value for a "black" light sensor reading

# loads the eeg data and din events from the h5 file
def load_data(h5_filename):
    with h5py.File(h5_filename, 'r') as f:
        
        # grab the eeg data
        eeg_group = f['eeg_data']
        eeg_data = eeg_group['eeg']
        eeg_samples = eeg_data[...]

        # grab the din data
        din_group = f['din_data']
        din_data = din_group['din']
        din_events = din_data[...]
        
    return eeg_samples, din_events

# takes the overall list of din values and only retains the ones that reflect
# the white square. This will be the first moment of change from the resting
# din state (value == 65535) to another din value
def modify_dins(din_events):
    updated_dins = []
    prev_din_value = din_events[0][2]
    for din in din_events:
        din_value = din[2] 
        if prev_din_value == din_off_value and din_value != din_off_value:
            updated_dins.append(din)
        prev_din_value = din_value
    return updated_dins

# saves data to the raw_data folder as mne raw object
def save_data(eeg_samples, updated_dins, stats_dict, raw_filename):

    # prepare mne file info and creating mne info object
    n_channels = 128
    ch_names = ['E' + str(i) for i in range(1, n_channels + 1)]
    ch_types = ['eeg'] * n_channels
    mne_info = mne.create_info(ch_names = ch_names, sfreq = sfreq, ch_types = ch_types)

    # convert to numpy arrays
    eeg_samples_array = np.array(eeg_samples).T

    # create raw object
    raw = mne.io.RawArray(eeg_samples_array, mne_info)

    # add the DIN events
    stim_data = np.zeros((1, len(raw.times)))
    info_stim = mne.create_info(['STI 014'], sfreq, ['stim'])
    stim_raw = mne.io.RawArray(stim_data, info_stim)
    raw.add_channels([stim_raw], force_update_info = True)

    # use the eeg start time as t = 0.0 and correct all events to reflect this
    # Furthermore, change the event ID's for the Dins to 1 and add events
    # to the raw object.
    start_time = stats_dict['eeg start']
    for din in updated_dins:
        din[0] -= start_time
        din[0] = round(din[0] * sfreq)
        din[2] = 1
    raw.add_events(updated_dins, 'STI 014', replace = True)

    # save the raw file
    raw.save(raw_filename, overwrite = True)


# pull chunks of data from eeg outlet and save in "eeg_samples" array
def pull_chunks(inlet_eeg, stats_dict, h5_filename):

    with h5py.File(h5_filename, 'w') as f:
        # create our groups and data sets for those groups
        eeg_group = f.create_group('eeg_data')
        din_group = f.create_group('din_data')

        eeg_data = eeg_group.create_dataset('eeg',(0,128), maxshape = (None,128), chunks = True, dtype = 'float64')
        din_data = din_group.create_dataset('din',(0,3), maxshape = (None,3), chunks = True, dtype = 'float64')

        found_first_eeg_sample = False
        index = 0
        while True:
            try:
                # pull our chunk
                new_samples_old, new_timestamps = inlet_eeg.pull_chunk()
                new_samples = np.array(new_samples_old)

                # skip if empty chunk
                if len(new_samples) == 0:
                    continue

                # store the timestamp of the very first eeg sample that we save
                if found_first_eeg_sample == False:
                    stats_dict['eeg start'] = float(new_timestamps[0])
                    found_first_eeg_sample = True

                # separate and store the eeg and DIN data
                eeg_samples = new_samples[:, :-1]
                din_samples = new_samples[:, -1]

                # rescale our data lists
                new_index = index + len(new_timestamps)
                eeg_data.resize((new_index, 128))
                din_data.resize((new_index, 3))

                # add our new eeg data
                eeg_data[index:new_index] = eeg_samples

                # add our new din events
                new_din_events = []
                for din_sample, timestamp in zip(din_samples, new_timestamps):
                    din_event = [float(timestamp), float(0), float(din_sample)]
                    new_din_events.append(din_event)
                din_data[index:new_index] = np.array(new_din_events)

                # update our current current index
                index = new_index

            except Exception as e:
                del inlet_eeg
                f.close()
                break

# find streams, collect eeg samples, save data
def eeg_inlet(stats_dict, subject_num):

    # preparing the save paths
    rel_path = os.path.dirname(__file__)
    
    # path/filename for saving chunks in h5 file
    h5_folder_path = os.path.join(rel_path, 'h5_data')
    h5_filename = os.path.join(h5_folder_path, subject_num + '_eeg.h5')
    
    # path/filename for saving eeg/DIN data as MNE raw objects
    raw_folder_path = os.path.join(rel_path, 'raw_data')
    raw_filename = os.path.join(raw_folder_path, subject_num + '_raw.fif')
    
    # create the h5 save path if it does not exist
    if not os.path.exists(h5_folder_path):
        os.mkdir(h5_folder_path)
    
    # create the raw save folder if it does not exist
    if not os.path.exists(raw_folder_path):
        os.mkdir(raw_folder_path)
    
    # find eeg stream
    print('\n\nLooking for EEG stream....\n\n')
    eeg_streams = resolve_stream('type', 'EEG')
    eeg_stream_name = eeg_streams[0].name()
    print('\n\nFound EEG stream named %s\n\n.'%eeg_stream_name)

    # initialize the inlet
    inlet_eeg = StreamInlet(eeg_streams[0], recover = False)
    stats_dict['eeg stream initialized'] = True

    # wait until both the marker and eeg inlets are initialized
    while stats_dict['event stream initialized'] == False:
        pass

    # collect our data
    pull_chunks(inlet_eeg, stats_dict, h5_filename)

    # load our eeg data and din events
    eeg_samples, din_events = load_data(h5_filename)

    # collect the proper dins (when there was actually a flash)
    updated_dins = modify_dins(din_events)

    # save the data as mne raw object
    save_data(eeg_samples, updated_dins, stats_dict, raw_filename)