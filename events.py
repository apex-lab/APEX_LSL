# Written by David Falk (UChicago APEX Lab) to collect data from MOT task.
# This file collects the event data and stores it in a file for later use in the
# inlets.py function
from pylsl import StreamInlet, resolve_stream, local_clock
import numpy as np
import os

# Create tag dicts so that tags and associated numbers get printed
# on screen so that they experimenter knows the code is running
# properly
def tag_dicts():
    
    # initialize forwards and reverse dictionaries
    tag_dict = {}
    rev_tag_dict = {}
    
    # Fixed Tags
    tags = ['Time Up', 'Game Stop', 'Escape Key', 'Space Key', 'Click', 'Unclick', 
            'Movement Stop', 'Correct', 'Game start', 'Balls Flashing', 'Movement Start', 
            'First Eyes Open Start', 'First Eyes Open Stop', 'Second Eyes Open Start',
            'Second Eyes Open Stop', 'First Eyes Closed Start', 'First Eyes Closed Stop',
            'Second Eyes Closed Start', 'Second Eyes Closed Stop']
    
    # tag for end of event stream
    tag_dict['Terminate Event Stream'] = '0'
    
    # add the fixed tags to the dict
    for index, tag in enumerate(tags):
        tag_dict[tag] = str(index + 2)
    length = int(tag_dict['Second Eyes Closed Stop'])

    # Fixation tags
    for i in range(1,100):
        tag = 'FX%s'%str(i)
        if len(tag) < 4:
            tag += 'X'
        tag_dict[tag] = str(length + i)
    length = int(tag_dict['FX99'])
    
    # Miss tags
    k = 1
    for i in range(1, 10):
        for j in range(0, i):
            tag = 'MS%d%d'%(j,i)
            tag_dict[tag] = str(length + k)
            k += 1

    # Create reverse dictionary
    for tag, number_string in tag_dict.items():
        rev_tag_dict[number_string] = tag
    return tag_dict, rev_tag_dict

# saves our events into the event_data folder
def save_events(collected_data, filename):

    # storing our array in the array folder
    collected_data_new = np.array(collected_data.copy())
    np.save(filename, collected_data_new)

# pulling samples and adding to our array
def pull_samples(inlet_events, stats_dict, rev_tag_dict):
    collected_data = []
    while True:
        event, timestamp = inlet_events.pull_sample()
        correction = inlet_events.time_correction()
        print('Event Name: %s ..... Event Number: %s'%(rev_tag_dict[event[0]], event[0]))
        if event[0] == "0":
            del(inlet_events)
            break
        else:
            if len(collected_data) == 0:
                stats_dict['trigger start'] = local_clock()
            corrected_timestamp = timestamp + correction
            collected_data.append([corrected_timestamp, 0, int(event[0])])
    return collected_data

# pull events and save data
def event_inlet(stats_dict, subject_num):
    
    # file paths for storing event data
    rel_path = os.path.dirname(__file__)
    save_path = os.path.join(rel_path, 'event_data')
    filename = os.path.join(save_path, subject_num + '.npy')

    # create save folder if necessary
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    
    # create relevant tag dictionaries
    tag_dict, rev_tag_dict = tag_dicts()
    
    # finding stream
    print('\n\nLooking for MOT event stream...\n\n')
    streams_events = resolve_stream('name', 'event_stream')
    print('\n\nfound MOT event Stream named %s\n\n'%(streams_events[0].name()))

    # initializing the inlet
    inlet_events = StreamInlet(streams_events[0], recover = False)
    stats_dict['event stream initialized'] = True

    # wait until eeg and marker stream have been initialized
    while stats_dict['eeg stream initialized'] == False:
        pass

    # pull samples until event outlet stream closes
    collected_data = pull_samples(inlet_events, stats_dict, rev_tag_dict)

    # save our events to the event_data folder
    save_events(collected_data, filename)