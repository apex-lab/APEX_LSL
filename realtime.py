import mne
import mne_realtime
import threading
import multiprocessing
from pylsl import StreamInfo, StreamInlet, StreamOutlet, resolve_stream, local_clock
import os

Flash_Time = 2.00 # length of flash epoch

def tag_dicts():
    # still need miss and fixation tags
    tags = ['TMUP', 'STOP', 'ESCP', 'SPCE', 'CLCK', 'UCLK', 'MVE1', 'CRCT', 'STRT', 'FLSH', 'MVE0', 
    'OPN0', 'OPN1', 'OPN2', 'OPN3', 'CLS0', 'CLS1', 'CLS2', 'CLS3']
    tag_dict = {}
    tag_dict['Terminate Event Stream'] = '0'
    rev_tag_dict = {}
    for index, tag in enumerate(tags):
        tag_dict[tag] = str(index + 2)
    length = int(tag_dict['CLS3'])

    # create fixation tags
    for i in range(1,100):
        tag = 'FX%s'%str(i)
        if len(tag) < 4:
            tag += 'X'
        tag_dict[tag] = str(length + i)
    
    length = int(tag_dict['FX99'])
    # handle miss tags
    k = 1
    for i in range(1, 10):
        for j in range(0, i):
            tag = 'MS%d%d'%(j,i)
            tag_dict[tag] = str(length + k)
            k += 1

    for tag, number_string in tag_dict.items():
        rev_tag_dict[number_string] = tag
    return tag_dict, rev_tag_dict

def setup_streams():
    # set up our outlet (will ultimately return either a 0 or a 1 to MOT Task computer)
    outlet_info = StreamInfo('prediction_stream', 'events', 1, 0, 'string')
    prediction_outlet = StreamOutlet(outlet_info) 

    # set up our eeg/din inlet
    print('\n\nLooking for EEG stream\n\n')
    eeg_streams = resolve_stream('type', 'EEG')
    eeg_stream_name = eeg_streams[0].name()
    print('\n\nFound EEG stream named %s\n\n'%eeg_stream_name)
    eeg_inlet = StreamInlet(eeg_streams[0], recover = False)

    # set up our event inlet
    print('\n\nLooking for event stream\n\n')
    event_streams = resolve_stream('name', 'event_stream')
    print('\n\nFound event stream named %s\n\n'%event_streams[0].name())
    event_inlet = StreamInlet(event_streams[0], recover = False)

    while True:
        pass
    return prediction_outlet, eeg_inlet, event_inlet

def collect_data(eeg_inlet, eeg_data_dict):
    data = []
    while True:
        data, timestamps = eeg_inlet.pull_chunk()
        correction = eeg_inlet.time_correction()
        for timestamp in timestamps:
            timestamp += correction
        eeg_data_dict['data'].extend(data)
        eeg_data_dict['timestamps'].extend(timestamps)


# pull data from when we find the flash tag to roughly before flash ends
def pull_data(event_inlet, eeg_inlet, rev_tag_dict):
    
    # wait until we find the Flash tag to speed up later searches
    while True:
        tag, timestamp = event_inlet.pull_sample()
        if tag[0] == rev_tag_dict['FLSH']: # if the value sent translates to 'FLSH' in some sense
            break
    
    # collect data until we find Movement start
    start_time = local_clock()
    eeg_data = []
    eeg_timestamps = []
    while local_clock() - start_time < Flash_Time:
        data, timestamps = eeg_inlet.pull_chunk()
        correction = eeg_inlet.time_correction()
        for timestamp in timestamps:
            timestamp += correction
        eeg_data.extend(data)
        eeg_timestamps.extend(timestamps)
    return eeg_data, eeg_timestamps

            
# waits to find the start of the real trials before we begin recording
def find_start(event_inlet, rev_tag_dict):
    while True:
        tag, timestamp = event_inlet.pull_sample()
        correction = event_inlet.time_correction()
        timestamp += correction
        if tag[0] == rev_tag_dict['STRT']:
            return

# make a prediction and return either 0 or 1
def predict(eeg_data, eeg_timestamps):
    return

if __name__ == '__main__':
    tag_dict, rev_tag_dict = tag_dicts()
    
    # setup our inlets (EEG/DIN and Events) and our prediction outlets
    prediction_outlet, eeg_inlet, event_inlet = setup_streams()

    # wait to find the start of real trials
    find_start(event_inlet, rev_tag_dict)

    # repeat this process of finding the relevant data, trimming that data,
    # and then predicting based on that data
    while True:
        # collect data
        eeg_data, eeg_timestamps = pull_data(event_inlet, eeg_inlet, rev_tag_dict)

        # make prediction
        prediction = predict(eeg_data, eeg_timestamps)

        # push to MOT task
        prediction_outlet.push_sample(str(prediction))