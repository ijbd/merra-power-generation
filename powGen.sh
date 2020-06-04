#!/bin/sh

# This is the shell driver for the powGen program. It simulates solar and wind power 
# by repeatedly running the Power_Generation_.8.py longitude by longitude. 




year=2018
log_file="log.tmp"
processed_merra_path="/scratch/mtcraig_root/mtcraig1/shared_data/merraData/resource/wecc/processed/"
processed_merra_name="cordDataWestCoastYear"$year".nc"
processed_merra_file=$processed_merra_path$processed_merra_name
destination_file_path="./"

python checkForFinish.py $log_file
finished=$?

pause 
while [ $finished -eq 0 ]
do
    python powGen_impl.py $log_file $year $processed_merra_file $destination_file_path
    python checkForFinish.py $log_file
    finished=$?
done
rm $log_file
echo "PowGen complete"
    