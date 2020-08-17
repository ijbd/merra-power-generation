# -*- coding: utf-8 -*-
"""
Created on 8/2/2020

@author: Julian Florez
"""

import numpy as np
import time as stopWatch
from netCDF4 import Dataset
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
import os

def generateBounds(regionFilename, latitudeRange, longitudeRange):
    """ Generates map of points in MERRA data that are in desired region or outside bounds for mapping to correct wind turbine classes
        (it is assumed that the dataset is in a rectangular shape)

    ...

    Args:
    ----------
    `regionFilename` (str): file path of netcdf bounds to be used and generate array

    `latitudeRange` (np array): contains range of specific latitudes for region of area of interest

    `longitudeRange` (np array): contains range of specific longitudes for region of area of interest


    """   
    rastData =  Dataset(regionFilename)

    #setting up values for raster data
    latsRast =  np.array(rastData["lat"][:])
    lonsRast =  np.array(rastData["lon"][:])
    regionOfInterest = np.array(rastData["Band1"][:][:])


    regionArray = np.zeros((len(longitudeRange),len(latitudeRange)))


    for lat in latitudeRange:
        closestLatIndex = np.where( np.abs(latsRast-lat) == np.abs(latsRast-lat).min())[0][0]
        for lon in longitudeRange:
            closestLonIndex = np.where( np.abs(lonsRast-lon) == np.abs(lonsRast-lon).min())[0][0]

            #If lat long of MERRA data box is offshore or in region (values 1 in raster) set them equal to 1 for master Array, else they are left as zeros
            if (regionOfInterest[closestLatIndex][closestLonIndex] == 1):
                latIndex = np.where(latitudeRange == lat)[0][0]
                lonIndex = np.where(longitudeRange == lon)[0][0]
                regionArray[lonIndex][latIndex] = 1


    #for debugging
    ''' 
    ax = sns.heatmap(regionArray)
    plt.show()
    '''
    return regionArray



def main(minLon, maxLon,minLat, maxLat, implementStateBounds = False):
    """ Generates map of points in MERRA data that are in desired region(s) or outside for mapping to correct wind turbine classes in case of offshore/onshore
        (it is assumed that the dataset is in a rectangular shape)

    ...

    Args:
    ----------
    `minLon` (float): minimum longitude value in MERRA dataset

    `maxLon` (float): maximum longitude value in MERRA dataset

    `minLat` (float): minimum latitude value in MERRA dataset

    `maxLat` (float): maximum latitude value in MERRA dataset

    `implementStateBounds` (bool): set to false, but if specifed as true, will read states bounds from folder (stateNetcdfs)
    and uses respective netCDF files to generate bounds
    """
    #setting up values for MERRA data latitude goes from min to max with .5 spacing while longitude is .625 spacing
    latitudeRange =  np.arange(minLat, maxLat+.5,0.5)
    longitudeRange =  np.arange(minLon,maxLon+0.625,0.625)
    #making sure all lons generated are less then the maxLon due to the .625 step
    longitudeRange = longitudeRange[longitudeRange <= maxLon]

    #reading in net cdf from shapefile that has lat and lon indices and whether location is on land or in water
    # water data is from https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-ocean/
    regionArray = np.zeros((len(longitudeRange),len(latitudeRange)))
    if implementStateBounds:
        stateFiles = os.listdir( os.path.abspath("stateNetcdfs"))
        #go state by state building up region array
        for stateFile in stateFiles:
            regionArray += generateBounds("stateNetcdfs\\" + stateFile,latitudeRange,longitudeRange)
    else:
        regionFilename = "offshoreBoundaries.nc"
        regionArray = generateBounds(regionFilename,latitudeRange,longitudeRange)
    
    #for debugging visuals
    '''
    ax = sns.heatmap(regionArray)
    plt.show()
    '''

    #changes numpy format to pandas for writing to xlsx
    df = pd.DataFrame(regionArray).T

    #need to enter filepath for writing to excel worksheet, format: rows: 0-36 (lat values) cols: 0 -30 (long values), shape is (37,31) for WECC
    #(0,0)-bottom left of united states in the ocean, (36,0)-top left near Washington!, (0,30)-bottom right edge of Texas, (36,30) top right near Montana
    if implementStateBounds:
        filePath = "state_MERRA_Format_Bounds.xlsx"
    else:
        filePath = "offshore_MERRA_Format_Bounds.xlsx"

    try:
        df.to_excel(excel_writer = filePath)
    except:
        error_message = "Trying to write to %s but a problem occurred! (change name of already present file or move to different directory)" % (filePath)
        raise FileExistsError(error_message)
    print("Wrote data to: %s" % (filePath))
