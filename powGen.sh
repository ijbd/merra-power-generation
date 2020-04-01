#!/bin/sh

# This is the shell driver for the powGen program. It simulates solar and wind power 
# by repeatedly running the Power_Generation_.8.py longitude by longitude. 

python checkForFinish.py
x=$?
while [ $x -eq 0 ]
do
    python Power_Generation_.8.py
    python checkForFinish.py
    x=$?
done
echo "PowGen complete"
    