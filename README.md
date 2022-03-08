# Drought index
Computes the drought index from **monthly** rasters

**Input Data**

  - R1H: [1981 - 2021]
  - VIM: [2002 - 2021]
  - TDA: [2002 - 2021]
  - DLX: [1981 - 2021]
  - SOS: [2002 - 2021]

  - R1H smoothed: LTA of smoothed R1H data

**Algorithm**

  - Weights

Computed from R1H smoothed.

We select R1H smoothed rasters within the months of interest (R1H_smoothed_sel)

weights = R1H_smoothed_sel/sum(R1H_smoothed_sel)

  - Processing
 
We compute the Qrfh, Qvim, Qtda, Qdlx and Qsos (and teta respectively).

We derive Qmulti.

(see *SeasonalDroughtHazardIndex.pptx*)
  
 
 **Running script**
 
 To run the script the user must run **within the Conda environment** the command line:
 *python drought_index.py date1 date2*
 
with *date1* and *date2* the *yyyymm* begin and end date of the analysis.

Example: *python drought_index.py 202110 202112*
