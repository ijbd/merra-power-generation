#!/usr/bin/env python

# This helper program checks a log file to determine whether or not the power generation process is complete.

import os, sys
from os import path

if path.exists(sys.argv[1]) != True:
    sys.exit(0)
else:
    l = open(sys.argv[1])
    for line in l:
        if(line == "done"):
            sys.exit(1)
            quit()
    sys.exit(0)
