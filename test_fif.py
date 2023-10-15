import mne

if __name__ == '__main__':
    filepath = '/home/john/Desktop/Neuroadapt APTIMA project tasks/multipleobjecttrackingexperiment-master/mot_nback_exp/raw_data/99_raw.fif'
    raw = mne.io.read_raw_fif(filepath, preload=True)
    print(raw.info)
    events = mne.find_events(raw)
    for event in events:
        print(event)
