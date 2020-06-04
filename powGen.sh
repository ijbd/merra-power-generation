#!/bin/sh

# This is the shell driver for the powGen program. It simulates solar and wind power 
# by repeatedly running the Power_Generation_.8.py longitude by longitude. 




year=2018
region="wecc"
log_file="log.tmp"

python checkForFinish.py $log_file
finished=$?

while [ $finished -eq 0 ]
do
    python powGen_impl.py $year $region $logfile
    python checkForFinish.py $log_file
    finished=$?
done
rm $log_file
echo "PowGen complete"
    