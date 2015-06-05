'''
ACTDR

Aggregated CTD reader

Reads in NOAA and IOS data
'''
import ios_ctd
import dateutil.parser
import seawater as SW
import numpy as np
import csvWOD
import os
import pickle

STANDARD_KEYS = ['Longitude','Latitude','ID','Day','Month','Year','Temperature','Salinity','Depth']
IOS_DAT_CONV_KEYS = {'Temperature:Primary' : 'Temperature', 'Temperature:Secondary' : 'Temp2', 'Salinity:T0:C0' : 'Salinity', 'Temperature' : 'Temperature', 'Salinity' : 'Salinity'}

CTD_DAT = []

def save_dat(fnm):
    '''
    save_dat
    
    Function used to pickle python data
    '''
    global CTD_DAT, STANDARD_KEYS
    
    print '> open ', fnm
    # open the file
    fid = open(fnm,'wb')
    
    # dump in order : CTD_DAT then STANDARD_KEYS
    
    print '> dump CTD_DAT'
    pickle.dump(CTD_DAT,fid)
    print '> dump STANDARD_KEYS'
    pickle.dump(STANDARD_KEYS,fid)
    
    # close file
    print '> close ', fnm
    fid.close()
    print '> complete'
    
def load_dat(fnm):
    '''
    load_dat
    
    Loads the pickled data from save_dat
    '''
    global CTD_DAT, STANDARD_KEYS
    
    print '> delete global CTD_DAT'
    reset_global()
    
    print '> open ', fnm
    fid = open(fnm,'rb')
    
    print '> load CTD_DAT'
    CTD_DAT = pickle.load(fid)
    print '> load STANDARD_KEYS'
    STANDARD_KEYS = pickle.load(fid)
    
    print '> close ', fnm
    fid.close()
    print '> complete'

def reset_global():
    del CTD_DAT[:]

def load_ios():
    '''
    load_ios
    
    Loads in all the ios data into the CTD_DAT list and converts to ACTDR standard format.
    '''
    global CTD_DAT
    
    DIR = '/ocean/rirwin/2_FALKOR_Data/6_IOS_Data/'
    filenames = [DIR+f for f in os.listdir(DIR) if (f.endswith('che') or f.endswith('bot') or f.endswith('ctd') or f.endswith('CTD') or f.endswith('CHE') or f.endswith('BOT'))]

    for count,filename in enumerate(sorted(filenames)):
        print '> reading ', filename
        dat = ios_ctd.ios_read(filename)        
        print '> success'
        
        print '> convert and append'
        tmp = convert_ios_dict(dat)
        if tmp is None:
            print '> ERROR :: CONVERT FAILED, NOT APPENDED'
        else:
            CTD_DAT.append(tmp)
        print '> success'
        
def load_noaa():
    '''
    load_noaa
    
    Loads in the csvWOD database. Takes a while, is slow.
    '''
    global CTD_DAT
    
    DIR = '/ocean/rirwin/2_FALKOR_Data/5_WOD13_Data/WOD13_004/'
    filenames = [DIR+f for f in os.listdir(DIR) if (f.endswith('csv'))]
    #filenames = [DIR+'ocldb1432579402.10924.CTD5.csv']

    for count,filename in enumerate(sorted(filenames)):
        print '> reading ', filename
        noaa_casts = csvWOD.read_casts(filename)
        print '> success'
        
        print '> convert and append'
        for dat in noaa_casts:
            tmp = convert_noaa_dict(dat)
            if tmp is None:
                print '> ERROR :: CONVERT FAILED, NOT APPENDED'
            else:
                CTD_DAT.append(tmp)
        print '> success'

def remove_duplicates():
    '''
    remove_duplicates
    
    Removes any duplicate cast information shared between the NOAA and IOS databases
    '''
    global CTD_DAT
    
    # acquire all duplicate indices
    dupl_inds = []
    
    # loop through each cast and the remainder of the list
    for cnt1,cast1 in enumerate(CTD_DAT[:-1]):
        for cnt2,cast2 in enumerate(CTD_DAT[cnt1+1:]):
            # compare IDs -- if they are equivalent, then its considered a duplicate
            if cast1['ID'] == cast2['ID']:
                # keep the cast with the most information
                if cast1['Temperature'] is None:
                    dupl_inds.append(cnt1)
                if cast2['Temperature'] is None:
                    dupl_inds.append(cnt1+cnt2+1)
                if cast1['Temperature'] is not None and cast2['Temperature'] is not None:
                    if len(cast2['Temperature']) > len(cast1['Temperature']):
                        dupl_inds.append(cnt1)
                    else:
                        dupl_inds.append(cnt1+cnt2+1)
                print '> DUPLICATE IDS ', cast1['ID']
    
    # remove any duplicate entries of the duplicates
    # e.g. this may happen if a BOT cast has the same ID as a CHE and CTD cast in the IOS database
    #      - there would be 3 ID's, and the one with the fewest depth entries might be listed twice
    dupl_inds = list(set(dupl_inds))
    
    # loop through the duplicate list in reverse, so that indices are consistent
    dupl_inds = sorted(dupl_inds)[::-1]
    for ii in dupl_inds:
        del CTD_DAT[ii]

def convert_ios_dict(dat):
    '''
    convert_ios_dict
    
    Converts an ios_ctd.ios_read dictionary object to a standardized
    dictionary object.
    
    So far the stand
    '''
    global STANDARD_KEYS, IOS_DAT_CONV_KEYS
    
    new_dat = {}
    
    # initialize the new object
    for key in STANDARD_KEYS:
        new_dat[key] = None
    
    # code to convert ios data here
    
    # longitude/latitude are floats, no need to convert
    new_dat['Longitude'] = dat['Longitude'] 
    new_dat['Latitude'] = dat['Latitude']
    
    # Day/Month/Year determined by parsing Date string
    date_str = dat['Date']
    dt_obj = dateutil.parser.parse(date_str)
    new_dat['Day'] = dt_obj.day
    new_dat['Month'] = dt_obj.month
    new_dat['Year'] = dt_obj.year
    
    # ID is the complicated one, need to compare to available NOAA data
    # -- this is necessary to determine whether two casts are repeated
    
    # FMT: YR   MNTH DAY  LONG      LAT
    #      4chr 2chr 2chr 3chr.2chr 2chr.2chr
    # it is a 17 character unique identifier
    new_dat['ID'] = '%04d%02d%02d%03.2f%02.2f' % (new_dat['Year'], new_dat['Month'], new_dat['Day'], np.abs(new_dat['Longitude']), np.abs(new_dat['Latitude']))
    # remove the decimal point from lat and lon
    new_dat['ID'] = new_dat['ID'].replace('.','')
    
    for count, var in enumerate(dat['Variables']):
        # convert from pressure to depth
        if 'Pressure' in var['Name']:
            # need to use Seawater package to convert
            # from dbar to depth***
            new_dat['Depth'] = []
            for ii in dat['DATA'][count]:
                new_dat['Depth'].append(SW.dpth(ii,new_dat['Latitude']))
            continue
        # otherwise, use the conversion keys to set data
        for key,val in IOS_DAT_CONV_KEYS.iteritems():
            # make sure we haven't already written this variable
            # -- happens on occasion when Temperature:Primary and
            #    Temperature:Secondary are both available
            if var['Name'] == key and val in new_dat:
                if new_dat[val] is None or len(new_dat[val]) == 0:
                    new_dat[val] = dat['DATA'][count]
                break
    
    # archaic error handling for now
    if 'Temperature' not in new_dat:
        print '> ERROR :: TEMP ENTRY NOT FOUND'
        return None
    
    if 'Salinity' not in new_dat:
        print '> ERROR :: SALN ENTRY NOT FOUND'
        return None
    
    if 'Depth' not in new_dat:
        print '> ERROR :: PRESS ENTRY NOT FOUND'
        return None
    
    return new_dat
    
def convert_noaa_dict(dat):
    '''
    convert_NOAA_dict
    
    Converts a NOAA dictionary object to a standardized
    dictionary object.
    '''
    global STANDARD_KEYS, IOS_DAT_CONV_KEYS
    
    new_dat = {}
    
    # initialize the new object
    for key in STANDARD_KEYS:
        new_dat[key] = None
    
    # code to convert ios data here
    
    # longitude/latitude are floats, no need to convert
    new_dat['Longitude'] = dat['Longitude'] 
    new_dat['Latitude'] = dat['Latitude']
    
    # Day/Month/Year determined by parsing Date string
    new_dat['Day'] = dat['Day']
    new_dat['Month'] = dat['Month']
    new_dat['Year'] = dat['Year']
    
    # ID is the complicated one, need to compare to available NOAA data
    # -- this is necessary to determine whether two casts are repeated
    
    # FMT: YR   MNTH DAY  LONG      LAT
    #      4chr 2chr 2chr 3chr.2chr 2chr.2chr
    # it is a 17 character unique identifier
    new_dat['ID'] = '%04d%02d%02d%03.2f%02.2f' % (new_dat['Year'], new_dat['Month'], new_dat['Day'], np.abs(new_dat['Longitude']), np.abs(new_dat['Latitude']))
    # remove the decimal point from lat and lon
    new_dat['ID'] = new_dat['ID'].replace('.','')
    
    if 'Temperatur' in dat:
        new_dat['Temperature'] = dat['Temperatur']
    else:
        print '> ERROR :: TEMP ENTRY NOT FOUND'
        return None
    
    if 'Salinity' in dat:
        new_dat['Salinity'] = dat['Salinity']
    else:
        print '> ERROR :: SALN ENTRY NOT FOUND'
        return None
        
    if 'Depth' in dat:
        new_dat['Depth'] = dat['Depth']
    else:
        print '> ERROR :: DPTH ENTRY NOT FOUND'
        return None
    
    return new_dat
    
