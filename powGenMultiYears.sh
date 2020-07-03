#!/bin/bash

region="wecc"

for year in {2016..2018}
do
     echo "Running:" $year $region
     sbatch powGen.sbat $year $region
done
echo "Multiyear complete."