import ACTDR
import numpy as np
from scipy.interpolate import griddata
import scipy.io as sio

def filter_CTD_list(filt_type,vmin,vmax=0):
    '''
    filter_CTD_list
    
    Takes 3 arguments, returns a list of casts filtered from
    ACTDR.CTD_DAT.
    
    filt_type - a string that defines how the list will be filtered
         Valid strings
         MONTH  - filters by month, vmin, vmax scalars
         YEAR   - filters by year, vmin, vmax scalars
         REGION - filters by rectangular region, vmin, vmax size 2 arrays/lists
    '''
    
    flist = []
    if filt_type == 'MONTH':
        if vmax == 0: vmax = vmin
        
        for ii,cast in enumerate(ACTDR.CTD_DAT):
            if cast['Month'] >= vmin and cast['Month'] <= vmax:
                flist.append(cast)
    elif filt_type == 'YEAR':
        if vmax == 0: vmax = vmin
        
        for ii,cast in enumerate(ACTDR.CTD_DAT):
            if cast['Year'] >= vmin and cast['Year'] <= vmax:
                flist.append(cast)
    elif filt_type == 'REGION':
        if len(vmin) != 2 or len(vmax) != 2:
            print '> ERROR :: vmin and vmax must be lists of length 2 for REGION'
            return None
        
        for ii,cast in enumerate(ACTDR.CTD_DAT):
            if cast['Longitude'] >= vmin[0] and cast['Latitude'] >= vmin[1] and \
                cast['Longitude'] <= vmax[0] and cast['Latitude'] <= vmax[1]:
                flist.append(cast)
    else:
        print '> ERROR :: unexpected filter type'
        return None
    
    return flist

def get_TS_hist(casts,Sbins,Tbins):
    '''
    get_TS_hist
    
    Returns the T/S historgram in the cast list
    Uses Sbins and Tbins to specify the edges of bins
    used in the histogram.
    '''
    Tlist = [y for x in casts for y in x['Temperature']]
    Slist = [y for x in casts for y in x['Salinity']]
           
    hist = np.histogram2d(Slist,Tlist,bins=[Sbins,Tbins])[0]
    return hist

def get_mode_ind(hist):
    '''
    get_mode_ind
    
    Returns the index of the highest frequency bin.
    '''
    IND = np.unravel_index(hist.argmax(), hist.shape)
    return IND

def get_bin_dat(casts,SbinL,SbinR,TbinL,TbinR):
    '''
    get_bin_dat
    
    Returns all casts that contain data within a specified bin.
    
    match_dat is the return value --- a list of casts (dictionary objects)
    '''
    match_dat = []
    for cast in casts:
        for ii in range(0,len(cast['Depth'])):
            if cast['Temperature'][ii] >= TbinL and cast['Temperature'][ii] < TbinR \
               and cast['Salinity'][ii] >= SbinL and cast['Salinity'][ii] < SbinR:
                # we have a cast that belongs
                match_dat.append(cast)
                break
    return match_dat
    
def get_TSmode(cast_inf,Sbins=np.arange(33,35.1,0.25),Tbins=np.arange(4,12,1)):
    '''
    get_TSmode
    
    Returns the TS mode casts and properties.
    '''
    hist = get_TS_hist(cast_inf,Sbins,Tbins)

    modeIND = get_mode_ind(hist)
    modeDAT = get_bin_dat(cast_inf,Sbins[modeIND[0]],Sbins[modeIND[0]+1],Tbins[modeIND[1]],Tbins[modeIND[1]+1])    

    return Sbins,Tbins,modeDAT,modeIND

def get_var_at_isopyc(cast,sigT,var_nm):
    '''
    get_var_at_isopyc
    
    Returns an interpolated variable at an isopycnal sigma_t value.
    Returns NaN if not found / out of range.
    '''
    if max(cast['sigmaT']) > sigT and min(cast['sigmaT']) < sigT:
        if var_nm in cast:
            #nans,x = nan_helper(cast['sigmaT'])
            #cast['sigmaT'] = np.interp(x(nans),x(~nans),cast['sigmaT'][~nans])
            return np.interp(sigT,cast['sigmaT'],cast[var_nm])
        else:
            print 'Key ', var_nm, ' not found.'
            return np.nan
    else:
        return np.nan
    
def get_var_at_depth(cast,dpth,var_nm):
    '''
    get_var_at_depth
    
    Returns an interpolated variable at a depth value.
    Returns NaN if not found / out of range.
    '''
    if max(cast['Depth']) > dpth and min(cast['Depth']) < dpth:
        if var_nm in cast:
            return np.interp(dpth,cast['Depth'],cast[var_nm])
        else:
            print 'Key ', var_nm, ' not found.'
            return np.nan
    else:
        return np.nan

def get_all_vars_at_isopyc(cast_inf,sigT,var_nm):
    '''
    get_all_vars_at_isopyc
    
    Returns all instances of variable var_nm at isopycnal sigT.
    '''
    all_vars = []
    for cast in cast_inf:
        val = get_var_at_isopyc(cast,sigT,var_nm)
        if ~np.isnan(val):
            all_vars.append({var_nm : val, 'Latitude' : cast['Latitude'], 'Longitude' : cast['Longitude'], 'Year' : cast['Year'], 'Month' : cast['Month']})
    return all_vars
    
def get_all_vars_at_depth(cast_inf,dpth,var_nm):
    '''
    get_all_vars_at_depth
    
    Returns all instances of variable var_nm at depth dpth.
    '''
    all_vars = []
    for cast in cast_inf:
        val = get_var_at_depth(cast,dpth,var_nm)
        if np.isnan(val) == False:
            all_vars.append({var_nm : val, 'Latitude' : cast['Latitude'], 'Longitude' : cast['Longitude']})
    return all_vars

def get_grid_data(info,lon_region,lat_region,var_nm,interp='nearest'):
    '''
    get_grid_data
    
    Interpolate a set of unordered points onto a regular grid. 
    info -- list of CTD casts
    lat/lon_region -- the regular grid to be interpolated onto
    var_nm -- the variable name of interest
    '''
    x = np.array([k['Longitude'] for k in info])
    y = np.array([k['Latitude'] for k in info])
    z = np.array([k[var_nm] for k in info])

    pts = np.array([x,y]).transpose()
    
    grid_dat = griddata(pts, z, (lon_region, lat_region), method=interp)
    return grid_dat

def get_isopyc_surface(info,sigT,var_nm,lon_dat,lat_dat,Nlon=50,Nlat=50,interp='nearest'):
    '''
    get_isopyc_surface
    
    Returns a regular grid of variable var_nm on isopycnal surface sigT. 
    Data is interpolated from all casts in info.
    '''
    lon_region,lat_region = np.meshgrid(np.linspace(lon_dat[0],lon_dat[1],Nlon),np.linspace(lat_dat[0],lat_dat[1],Nlat))
    sigT_filt = get_all_vars_at_isopyc(info,sigT,var_nm)
    print '> using ', len(sigT_filt), ' cast data'
    grid_dat = get_grid_data(sigT_filt,lon_region,lat_region,var_nm,interp)
    
    return (lon_region,lat_region,grid_dat,sigT_filt)

def get_depth_surface(info,dpth,var_nm,lon_dat,lat_dat,Nlon=50,Nlat=50,interp='nearest'):
    '''
    get_depth_surface
    
    Returns a regular grid of variable var_nm on depth surface dpth. 
    Data is interpolated from all casts in info.
    '''
    lon_region,lat_region = np.meshgrid(np.linspace(lon_dat[0],lon_dat[1],Nlon),np.linspace(lat_dat[0],lat_dat[1],Nlat))
    dpth_filt = get_all_vars_at_depth(info,dpth,var_nm)
    grid_dat = get_grid_data(dpth_filt,lon_region,lat_region,var_nm,interp)
    
    return (lon_region,lat_region,grid_dat,dpth_filt)

def get_topo():
    '''
    get_topo
    
    Returns the topographic data in region around JdFE.
    '''
    topo=sio.loadmat('/ocean/rirwin/2_FALKOR_Data/3_Repo/topo/SouthVIgrid.mat')
    
    tDat = {'lon' : [], 'lat' : [], 'dpth' : []}
    
    tDat['lon'] = np.squeeze(np.array(topo['SouthVIgrid']['lon'][0][0]))
    tDat['lat'] = np.squeeze(np.array(topo['SouthVIgrid']['lat'][0][0]))
    tDat['dpth'] = np.squeeze(np.array(topo['SouthVIgrid']['depth'][0][0]))
    
    return tDat
