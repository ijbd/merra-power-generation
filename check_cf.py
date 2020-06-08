# ijbd:
# 
# Perform some basic checks on powGen output files. 

import numpy as np
import sys
from netCDF4 import Dataset

cf_root = "/scratch/mtcraig_root/mtcraig1/shared_data/merraData/cfs/"
region = sys.argv[1]
year = sys.argv[2]
type = sys.argv[3]

filename = cf_root + region + "/" + year + "_" + type + "_generation_cf.nc"

data = Dataset(filename)

cf = np.array(data.variables['cf'])

# print some stats

print("Maximum:", np.max(cf))
print("Minimum:", np.min(cf))
print("Average:", np.average(cf))
print("Valid Entries:", np.sum(np.logical_and(cf>=0,cf<=1)), "of", cf.size)