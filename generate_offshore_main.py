from generate_offshore_bounds import main 
import sys
import os
#input the min lon, max lon, min lat, and max lat in datset and script will generate excel file of whether datapoints are offshore (1) or onshore (0)
#excel sheet is then used in wind_class_generation where offshore can be assigned a separate value from onshore data (yet to be implemented).

#TO USE MANUAL: replace values for specific region (uses MERRA assumptions of lat being space .5 and lon being spaced .625)
#current values in are for WECC
'''
minLon = -125
maxLon = -106
minLat = 31.5
maxLat = 49.5
'''
minLon = float(input("Min lon: "))
maxLon = float(input("Max lon: "))
minLat = float(input("Min lat: "))
maxLat = float(input("Max lat: "))

main(minLon, maxLon,minLat, maxLat)
