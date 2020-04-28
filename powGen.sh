#!/bin/sh

# This is the shell driver for the powGen program. It simulates solar and wind power 
# by repeatedly running the Power_Generation_.8.py longitude by longitude. 

python checkForFinish.py
x=$?
year=2016
merra_folder="/scratch/mtcraig_root/mtcraig1/shared_data/merraData/resource/wecc/processed/"
merra_file="cordDataWestCoastYear2016"
destination_folder="/scratch/mtcraig_root/mtcraig1/shared_data/merraData/cfs/wecc/"
while [ $x -eq 0 ]
do
    python Power_Generation_.8.py $year $merra_folder $merra_file $destination_folder
    python checkForFinish.py
    x=$?
done
rm ./log.txt
echo "PowGen complete"
    