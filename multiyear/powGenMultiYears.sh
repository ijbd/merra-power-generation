#!/bin/bash

for dataYear in {2016..2018}
do
     echo "Running:" $dataYear
     sbatch powGen.sbat $dataYear
done
echo "Multiyear complete."