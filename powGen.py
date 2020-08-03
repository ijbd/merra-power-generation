import sys
import os
import numpy as np
from powGen_impl_beta import get_lat_lon
import wind_class_generation
import time
from netCDF4 import Dataset 

region=sys.argv[1]
start_year=int(sys.argv[2])
end_year=int(sys.argv[3])

#error handling
if start_year > end_year:
     print('Invalid start/end year')
     sys.exit(1)

# create IEC turbine class spreasheet if necessary:
root_directory = '/scratch/mtcraig_root/mtcraig1/shared_data/'
excelFilePath = root_directory + 'powGen/IEC_wind_class_'+region+'.xlsx'

# check for existing spreadsheet
if os.path.exists(excelFilePath):
     pass
else:
     print('Generating IEC turbine class spreadsheet before running slurm jobs. This shouldn\'t take more than a few minutes.')
     
     time.sleep(3)

     processed_merra_path = root_directory + 'merraData/resource/' + region + '/processed/'
     if region == "wecc": processed_merra_name = 'cordDataWestCoastYear'
     else: processed_merra_name = 'processedMERRA'
     processed_merra_file = processed_merra_path + processed_merra_name

     # get lat/lons
     lat = np.array(Dataset(processed_merra_file+str(start_year)+'.nc').variables['lat'])
     lon = np.array(Dataset(processed_merra_file+str(start_year)+'.nc').variables['lon'])

     #find all years of available resource data
     yearList = [int(filename[-7:-3]) for filename in os.listdir(processed_merra_path) if filename != processed_merra_name+'.nc' and filename.startswith(processed_merra_name)]

     latLength = len(lat)
     longLength = len(lon)
     rawDataFilePath = processed_merra_file

     #generates wind power class map based on IEC wind power classes, returns file path to which power class was written to
     wind_class_generation.main(np.sort(yearList), latLength, longLength, excelFilePath, rawDataFilePath)

print('Submitting batch jobs')
year = start_year
while year <= end_year:
     print("Running:", year, region)
     os.system('sbatch powGen.sbat '+str(year)+' '+region)
     year += 1

os.system('rm -r __pycache__/')