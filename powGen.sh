#!/bin/sh

# This is the shell driver for the powGen program. It simulates solar and wind power 
# by repeatedly running the Power_Generation_.8.py longitude by longitude. 

python checkForFinish.py
finished=$?
year=2018
logFile=2018_test_default_shear

while [ $finished -eq 0 ]
do
    python powGen_impl.py $year $logFile
    python checkForFinish.py
    finished=$?
done
rm $logFile
echo "PowGen complete"
    