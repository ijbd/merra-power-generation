from netCDF4 import Dataset
import numpy as np 
import sys

solar = Dataset(sys.argv[1])

ac = solar.variables['ac']

print("Min:", np.min(ac), "\nMax:", np.max(ac), "\nAverage:", np.average(ac)) 