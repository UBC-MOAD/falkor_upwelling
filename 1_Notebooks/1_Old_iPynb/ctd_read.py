import numpy as np
import dateutil.parser

def extract_quantities(line):
    index = np.int(line.partition(' ')[0])-1
    return index

def ctd_read(fnm):
    QUANTITIES = {'Pressure': 'Pressure','Temperature':'Temperature:Primary','Transmissivity':'Tranmissivity',
                  'Fluorescence': 'Fluorescence','Turbidity':'Turbidity','Salinity':'Salinity:T',
                  'Oxygen':'Oxygen:Voltage','Temperature':'Temperature:Secondary'}
    index = {}

    f = open(fnm, 'rt')
    print '> reading ', fnm
    date_inf = {}
    for line in f:
        line = line.strip()
        # look for start time
        if 'START TIME' in line:
            time = line.partition(' : ')[2]
            time = time.split(' ')[1] + ' ' + time.split(' ')[2]
            datep = dateutil.parser.parse(time)
            date_inf['Year'] = datep.year
            date_inf['Month'] = datep.month
            date_inf['Day'] = datep.day
        if line == '$TABLE: CHANNELS':
            break

    for line in f:
        line = line.strip()
        # find column listing
        for key, value in QUANTITIES.items():
            if value in line:
                index[key] = extract_quantities(line)
        if line == '$TABLE: CHANNEL DETAIL':
            #print index
            break
    
    station = '--'
    for line in f:
        line = line.strip()
        if 'LATITUDE' in line:
            latitude = line.partition(' : ')[2]
        elif 'LONGITUDE' in line:
            longitude = line.partition(' : ')[2]
        elif 'STATION' in line:
            station = line.partition(': ')[2]
        elif line.startswith('*INSTRUMENT') or line.startswith('*CALIBRATION'):
            break
            
    for line in f:
        line = line.strip()
        
        if '!' in line and '-1-' in line:
            words = line.split()
            delimiters = [len(w)+1 for w in words]
            break
            
    thedata = np.genfromtxt(f,delimiter=delimiters, skiprows=7)
    thedata = thedata.transpose()

    return (thedata,index,station,latitude,longitude,date_inf)
