#!/usr/bin/env python

# This helper program checks a log file to determine whether or not the power generation process is complete.

import os, sys
from os import path

inputData = sys.argv[1:] #exclude 1st item (script name)
logFile = inputData[0]
print('Log file:' + logFile,flush=True)

if path.exists(logFile) != True:
    sys.exit(0)
else:
    l = open(logFile)
    for line in l:
        if(line == "done"):
            sys.exit(1)
            quit()
    sys.exit(0)
