import argparse
import numpy as np
import rasterio as rio
import rioxarray as rx
from tqdm import tqdm

from functions import create_xarray, percentile, multiply_weights, get_months

import warnings
warnings.filterwarnings("ignore")



def main(begin:str, end:str):

	################
	# Loading Data #
	################

	path_rfh = 'Data/rfh'
	path_vim = 'Data/vim'
	path_tda = 'Data/tda'
	path_dlx = 'Data/dlx'
	path_sos = 'Data/sos'
	path_smoothed_rfh = 'Data/afsr1h_avgmmd3_smooth'

	da_rfh = create_xarray(path_rfh + '/*.tif')
	print('downloaded rfh')
	da_vim = create_xarray(path_vim + '/*.tif')
	print('downloaded vim')
	da_tda = create_xarray(path_tda + '/*.tif')
	print('downloaded tda')
	da_dlx = create_xarray(path_dlx + '/*.tif')
	print('downloaded dlx')
	da_sos = create_xarray(path_sos + '/*.tif')
	print('downloaded sos')

	das = [da_rfh, da_vim, da_tda, da_dlx]


	###########
	# Weights #
	###########

	# Weights computed from smoothed rfh data
	da_rfh_smooth = create_xarray(path_smoothed_rfh + '/*.rst', avg = True)

	# Selecting months of interest
	da_rfh_smooth_sel = da_rfh_smooth.sel(time = get_months(begin, end))

	# Creating mask
	ws = da_rfh_smooth_sel.sum('time')
	w_mask = ws.where(ws == 0, 1)

	# Computing weights
	weights = da_rfh_smooth_sel / ws
	weights = weights.rename({'time': 'month'})



	##############
	# Processing #
	##############

	# Defining period
	begin_date = begin[0:4] + '-' + begin[4:6] + '-01'
	end_date = end[0:4] + '-' + end[4:6] + '-28'

	Qs = []

	# RFH, VIM, TDA, DLX
	for i,da in tqdm(enumerate(das)):
	    
	    # Deriving percentile
	    Q = da.groupby(da.time.dt.strftime("%m")).apply(percentile)
	    Q = Q / 100
	    
	    # inverting for TDA and DLX
	    if i in [2,3]:
	        Q = 1 - Q
	    
	    # Cropping to period of interest
	    Q = Q.sel(time=slice(begin_date, end_date))
	    
	    # Converting percentile to logit
	    teta = np.log(Q / (1 - Q))

	    # Multiplying by weights
	    teta = multiply_weights(teta, weights)
	    teta = teta.sum('time')
	    
	    # Reconverting to percentile
	    Q = 100 * (np.exp(teta) / (1 + np.exp(teta)))
	    
	    # Multiplying by mask
	    Q = Q * w_mask.values
	    
	    Qs.append(Q)

	    
	# SOS
	Qsos = percentile(da_sos)
	Qsos = Qsos / 100
	Qsos = 1 - Qsos
	tetasos = np.log(Qsos / (1 - Qsos))
	Qsos = Qsos.sel(time=Qsos.time.dt.year.isin([int(begin[0:4])]))*100
	Qsos = Qsos[0] * w_mask.values


	# QMULTI
	
	[Qrfh, Qvim, Qtda, Qdlx] = Qs

	coef_rfh = 0.15
	coef_vim = 0.15
	coef_tda = 0.25
	coef_dlx = 0.25
	coef_sos = 0.2

	Qmulti = Qrfh.copy()
	Qmulti.values = coef_rfh * Qrfh.values + coef_vim * Qvim.values + coef_tda * Qtda.values + coef_dlx * Qdlx.values + coef_sos * Qsos.values


	##################
	# Exporting data #
	##################

	# Qrf, Qvi, Qtd, Qdl
	types = ['qrf', 'qvi', 'qtd', 'qdl']
	for i,Q in enumerate(Qs):
	    name = 'Export_Data/moz' + types[i] + begin[0:4] + '01d1.tif'
	    Q.rio.to_raster(name)

	# Qso
	name = 'Export_Data/mozqso' + begin[0:4] + '01d1.tif'
	Qsos.rio.to_raster(name)

	# Qml
	name = 'Export_Data/mozqml' + begin[0:4] + '01d1.tif'
	Qmulti.rio.to_raster(name)



if __name__ == '__main__':

	# Instantiate the parser
	parser = argparse.ArgumentParser(description='Compute drought index')

	# Input rasters to use for the mapping
	parser.add_argument('begin', type=str, help='Begin date')

	# Output rasters to map
	parser.add_argument('end', type=str, help='End date')

	# Parse
	args = parser.parse_args()

	main(args.begin, args.end)








