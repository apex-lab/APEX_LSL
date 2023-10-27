from pylsl import StreamInfo, StreamInlet, StreamOutlet, resolve_stream
import numpy as np

num_samples = 0 # change to however many samples we want

din_off_value = 65535 # din value when the light sensor is off

Movement_Code = '12' # event code for movement start
Correct_Code = '9' # code for a correct trial
Incorrect_Codes = list(range(120, 165)) # find these values
Level_Codes = list(range(21, 120)) # level codes
Start_Code = '10' # event code for start of real trials
Flash_Code = '11' # event code for flashes

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
    
    return prediction_outlet, eeg_inlet, event_inlet


# pull data from when we find the flash tag to roughly before flash ends
def pull_data(event_inlet, eeg_inlet):
    
    # Store the level
    while True:
        tag, = event_inlet.pull_sample()

        # Extract the level of the trial
        if int(tag[0]) in Level_Codes:
            level = tag[0].replace('F','')
            level = int(level.replace('X', ''))
            break
    
    # wait until we find the Flash tag to speed up later searches
    while True:
        tag, = event_inlet.pull_sample()

        # break once we find the beginning of the flash period
        if int(tag[0]) == Flash_Code:
            break
    
    # collect data for fixed number of samples
    length = 0
    prev_din_value = din_off_value 
    din_found = False
    eeg_data = np.array([])
    while True:
        # Separate into eeg and din samples
        samples_old, = eeg_inlet.pull_chunk()
        samples = np.array(samples_old)
        eeg_samples = samples[:, :-1]
        din_samples = samples[:, -1]

        # find our flash din and then start collecting data until
        # a predetermined number of samples is collected
        for din_sample, eeg_sample in zip(din_samples, eeg_samples):

            # don't start storing eeg data until we find the associated DIN
            # rests on the assumption that tags come before DINs
            # But all testing thus far shows this assumption holds
            cur_din_value = din_sample

            # Find first instance in the change of din values
            if not din_found:
                if prev_din_value == din_off_value and cur_din_value != din_off_value:
                    din_found = True
                if not din_found:
                    prev_din_value = cur_din_value
                    continue

            # keep adding eeg data until we hit the desired length then break
            # out of this for-loop
            # use a length variable as an int bc i think that will be quicker
            # than calculating the list length each time
            eeg_data.append(eeg_sample)
            length += 1

        # once we hit the desired length then break
        # out of this while-loop
        if length == num_samples:
            break
    
    return eeg_data, level

            
# waits to find the start of the real trials before we begin recording
def find_start(event_inlet):
    while True:
        tag, = event_inlet.pull_sample()
        if tag[0] == Start_Code:
            return

# make a prediction and return either 0 or 1
def predict(eeg_data):

    # insert your prediction code below
    prediction = 0
    return prediction

# get the result of the trial
def get_result(event_inlet):
    while True:
        tag, = event_inlet.pull_sample()
        if tag[0] == Correct_Code: # handles correct trials (1 for correct)
            return 1
        if int(tag[0]) in Incorrect_Codes: # handles incorrect trials (0 for incorrect)
            return 0

# performs the mid-trial clustering
def cluster(overall_array):
    # your clustering code here
    cluster = 0
    return cluster

if __name__ == '__main__':
    eeg_array = np.array([], dtype = 'float64')
    result_array = np.array([], dtype = 'int8')
    level_trial_array = np.array([], dtype = 'object')

    # setup our inlets (EEG/DIN and Events) and our prediction outlets
    prediction_outlet, eeg_inlet, event_inlet = setup_streams()

    # wait to find the start of real trials
    find_start(event_inlet)

    # repeat this process of finding the relevant data, trimming that data,
    # and then predicting based on that data
    trial = 1
    while True:
        # collect data
        eeg_data, level = pull_data(event_inlet, eeg_inlet)

        # make prediction
        prediction = predict(eeg_data)

        # push to MOT task
        prediction_outlet.push_sample(str(prediction))
        
        # grab the result of the trial
        result = get_result(event_inlet)

        # append the data, the trial, the level to their respective arrays
        np.append(eeg_array, eeg_data)
        np.append(result_array, result)
        np.append(level_trial_array, (trial, level))

        # cluster based on the existing data that we have
        clustering = cluster(np.array(eeg_array, result_array, level_trial_array))

        # each iteration of this loop represents one trial, so increment the trial variable
        # at the end of the loop
        trial += 1




