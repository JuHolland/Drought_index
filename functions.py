from datetime import date
import re

import glob
import numpy as np
import pandas as pd
from tqdm import tqdm
import xarray as xr

def filename_to_date(x: str, avg = False):
    '''
    Converts x string to dekadal date. 
    '''
    
    if not avg:
        
        try:
            dek = re.search(r'\d{4}\d{2}d\d{1}', x).group()
        except:
            dek = re.search(r'\d{4}\d{2}D\d{1}', x).group()
        
    
        # getting year, month and dekad
        year = int(dek[0:4])
        month = int(dek[4:6])
        d = dek[7:8]  

        if d=="1":
            greg_date = date(year,month,10)
        elif d=="2":
            greg_date = date(year,month,20)
        else:
            greg_date = date(year,month,28)
            
            
    else:
        
        dek = re.search(r'_avg\d{2}d3', x).group()
        
        greg_date = dek[4:6]

        greg_date = int(greg_date)

        
    return greg_date  


def percentile(da: xr.DataArray):
    '''
    Computes percentile of each pixel of an Xarray
    '''
    
    # Converting xarray to pd.DataFrame
    per_da = da.copy()
    da_np = da.values
    danp = da_np.reshape(len(da.time), len(da.x)*len(da.y))
    dapd = pd.DataFrame(danp)

    # Computing rank
    per = dapd.rank(method = 'min')
    per = (per - 1/3) / (len(da.time) + 1/3)

    # Reconverting to Xarray
    pernp = per.values
    per_np = pernp.reshape(da.shape)   
    per_da.values = per_np
    
    # Saving as int
    per_da = per_da * 100
    per_da = per_da.astype('int16')
    
    return per_da


def create_xarray(files_path, avg = False):
    '''
    Creates XArray from .tif or .rst files
    '''
    
    files = glob.glob(files_path)
    
    raster = xr.open_rasterio(files[0])
    aois = raster.values
    
    for file in tqdm(files[1:]):
        raster = xr.open_rasterio(file)
        aoi = raster.values
        
        aois = np.concatenate([aois, aoi])
    
    da = xr.DataArray(aois, dims = ['time', 'y', 'x'])

    # Get the timestamps from the filenames
    timestamps = [
            filename_to_date(file, avg)
            for file in files
        ]

    # Assign them to the time dimension:
    if not avg:
        da = da.assign_coords(time=pd.to_datetime(timestamps))
    else:
        da = da.assign_coords(time=timestamps)
    da = da.assign_coords(x=raster.x)
    da = da.assign_coords(y=raster.y)
    
    return da



def multiply_weights(da: xr.DataArray, weights: np.ndarray):
    '''
    Mutiplies Xarray by weights
    '''

    for i,d in enumerate(da):
        
        m = pd.to_datetime(d.time.values).month
        da[i] = d.values * weights.sel(month = m).values
        
    return da


def get_months(begin:str, end:str):
    '''
    Gets lists of months of interest from begin and end dates
    '''

    m1, m2 = int(begin[-2:]), int(end[-2:])
    
    if m1 < m2:
        m = list(range(m1, m2+1))
    else:
        m = list(range(m1, 13)) + list(range(1, m2+1))

    return m