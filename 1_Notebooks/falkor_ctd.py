import os
import numpy as np

DIRECTORY = '/ocean/rirwin/2_FALKOR_Data/7_Falkor_CTD/'

def extract_quantities(line):
    index = np.int(line.partition(' ')[0])-1
    return index
    
def falkor_ctd_dat(fnm):
    print '> ', fnm
    QUANTITIES = {'Pressure': 'Pressure','Temperature':'Temperature:Primary','Transmissivity':'Tranmissivity',
                  'Fluorescence': 'Fluorescence','Turbidity':'Turbidity','Salinity':'Salinity:T',
                  'Oxygen':'Oxygen:Voltage'}

    index = {}

    f = open(os.path.join(DIRECTORY, fnm), 'rt')
    for line in f:
        line = line.strip()
        # look for start time
        if 'START TIME' in line:
            time = line.partition(' : ')[2]
        if line == '$TABLE: CHANNELS':
            break
    for line in f:
        line = line.strip()
        # find column listing
        for key, value in QUANTITIES.items():
            if value in line:
                index[key] = extract_quantities(line) 
        if line == '$TABLE: CHANNEL DETAIL':
#            print index
            break
    for line in f:
        line = line.strip()
        if 'LATITUDE' in line:
            latitude = line.partition(' : ')[2]
        if 'LONGITUDE' in line:
            longitude = line.partition(' : ')[2]        
        if 'STATION' in line:
            station = line.partition(': ')[2]
#            print station
        if line == '*CALIBRATION':
            break
    for line in f:
        line = line.strip()
        if '$END' in line:
            break
    for line in f:
        line = line.strip()
        words = line.split()
        delimiters = [len(w)+1 for w in words] 
        break
    thedata = np.genfromtxt(f,delimiter=delimiters, skiprows=7)
    thedata = thedata.transpose()
        
    return (thedata,index,station,latitude,longitude)    
