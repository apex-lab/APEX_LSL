from pylsl import StreamInlet, resolve_stream, local_clock
import numpy as np
import os
import time

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
def pull_samples(inlet_events, stats_dict):
    collected_data = []
    offset_list = []
    #i = 1
    while True:
        event, timestamp = inlet_events.pull_sample()
        print(event[0])
        stats_dict['computer time offset'] = local_clock() - timestamp
        #if len(offset_list) < 10:
        #    offset_list.append(stats_dict['computer time offset'])
        #print(stats_dict['computer time offset'])
        #if i <= 10:
            #stats_dict['sample %d send/receive time'%i] = timestamp - stats_dict['sample %d pushed'%i]
            #stats_dict['sample %d timestamp'%i] = timestamp
        if event[0] == "0":
            #stats_dict['trigger stop'] = local_clock()
            inlet_events.close_stream()
            break
        else:
            if len(collected_data) == 0:
                stats_dict['trigger start'] = local_clock()
            corrected_timestamp = timestamp + stats_dict['computer time offset']
            collected_data.append([corrected_timestamp, 0, int(event[0])])
            #print(corrected_timestamp)
            #i += 1
    #print(offset_list)
    #print('mean offset: %f'%np.mean(offset_list))
    #print('std offset: %f'%np.std(offset_list))
    return collected_data

# pull events and save data
def event_inlet(stats_dict, subject_num):

    # finding stream
    print('\n\nLooking for MOT event stream...\n\n')
    streams_events = resolve_stream('name', 'event_stream')
    print('\n\nfound MOT event Stream named %s\n\n'%(streams_events[0].name()))

    # initializing the inlet
    inlet_events = StreamInlet(streams_events[0], recover = False)
    stats_dict['trigger inlet init stop'] = local_clock()
    stats_dict['event stream initialized'] = True

    while stats_dict['eeg stream initialized'] == False:
        pass
    # pull samples until event outlet stream closes
    collected_data = pull_samples(inlet_events, stats_dict)

    # save our events to the event_data folder
    save_events(collected_data, subject_num)

if __name__ == '__main__':
    event_inlet()
