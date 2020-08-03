import sys
import os
import numpy as np
from powGen_impl_beta import create_IEC_class

region=sys.argv[1]
start_year=int(sys.argv[2])
end_year=int(sys.argv[3])

#error handling
if start_year > end_year:
     print('Invalid start/end year')
     sys.exit(1)

create_IEC_class()

print('Submitting batch jobs')
year = start_year
while year <= end_year:
     print("Running:", year, region)
     #os.system('sbatch powGen.sbat '+str(year)+' '+region)
     year += 1