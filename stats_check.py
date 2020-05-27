from netCDF4 import Dataset
import numpy as np 
import sys

folder = sys.argv[1]

solar = Dataset(folder+"2018_solar_ac_generation.nc")
ac = solar.variables['ac']
print("Min:", np.min(ac), "\nMax:", np.max(ac), "\nAverage:", np.average(ac)) 
solar.close

wind = Dataset(folder+"2018_wind_ac_generation.nc")
ac = wind.variables['ac']
print("Min:", np.min(ac), "\nMax:", np.max(ac), "\nAverage:", np.average(ac)) 
wind.close