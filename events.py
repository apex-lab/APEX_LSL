from pylsl import StreamInlet, resolve_stream, local_clock
import numpy as np
import os
import time

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

# saves our events into the event_data folder
def save_events(collected_data, subject_num):
    # file paths for storing event data
    rel_path = os.path.dirname(__file__)
    save_path = os.path.join(rel_path, 'event_data')
    filename = os.path.join(save_path, subject_num + '.npy')

    # create save folder if necessary
    if not os.path.exists(save_path):
        os.mkdir(save_path)

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
    tag_dict, rev_tag_dict = tag_dicts()
    
    # finding stream
    print('\n\nLooking for MOT event stream...\n\n')
    streams_events = resolve_stream('name', 'event_stream')
    print('\n\nfound MOT event Stream named %s\n\n'%(streams_events[0].name()))

    # initializing the inlet
    inlet_events = StreamInlet(streams_events[0], recover = False)
    stats_dict['event stream initialized'] = True

    # wait until eeg and marker stream have been initialized
    #while stats_dict['eeg stream initialized'] == False:
    #    pass

    # pull samples until event outlet stream closes
    collected_data = pull_samples(inlet_events, stats_dict, rev_tag_dict)

    # save our events to the event_data folder
    save_events(collected_data, subject_num)

if __name__ == '__main__':
    event_inlet()
