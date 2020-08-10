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


def main(minLon, maxLon,minLat, maxLat):
    """ Generates map of points in MERRA data that are offshore or onshore for mapping to correct wind turbine classes
        (it is assumed that the dataset is in a rectangular shape)

    ...

    Args:
    ----------
    `minLon` (float): minimum longitude value in MERRA dataset

    `maxLon` (float): maximum longitude value in MERRA dataset

    `minLat` (float): minimum latitude value in MERRA dataset

    `maxLat` (float): maximum latitude value in MERRA dataset

    """


    #reading in net cdf from shapefile that has lat and lon indices and whether location is on land or in water
    # water data is from https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-ocean/
    regionFilename = "offshoreBoundaries.nc"

    rastData =  Dataset(regionFilename)

    #setting up values for raster data
    latsRast =  np.array(rastData["lat"][:])
    lonsRast =  np.array(rastData["lon"][:])
    regionOfInterest = np.array(rastData["Band1"][:][:])


    #setting up values for MERRA data latitude goes from min to max with .5 spacing while longitude is .625 spacing
    latsMERRA =  np.arange(minLat, maxLat+.5,0.5)
    lonsMERRA =  np.arange(minLon,maxLon+0.625,0.625)
    #making sure all lons generated are less then the maxLon due to the .625 step
    lonsMERRA = lonsMERRA[lonsMERRA <= maxLon]


    valuesMERRA = np.zeros((len(lonsMERRA),len(latsMERRA)))


    for lat in latsMERRA:
        closestLatIndex = np.where( np.abs(latsRast-lat) == np.abs(latsRast-lat).min())[0][0]
        for lon in lonsMERRA:
            closestLonIndex = np.where( np.abs(lonsRast-lon) == np.abs(lonsRast-lon).min())[0][0]

            #If lat long of MERRA data box is offshore (values 1 in raster) set them equal to 1 for master Array, else they are left as zeros
            if (regionOfInterest[closestLatIndex][closestLonIndex] == 1):
                latIndex = np.where(latsMERRA == lat)[0][0]
                lonIndex = np.where(lonsMERRA == lon)[0][0]
                valuesMERRA[lonIndex][latIndex] = 1


    #for debugging
    ''' 
    ax = sns.heatmap(valuesMERRA)
    plt.show()
    '''

    df = pd.DataFrame(valuesMERRA).T

    #need to enter filepath for writing to excel worksheet, format: rows: 0-36 (lat values) cols: 0 -30 (long values), shape is (37,31) for WECC
    #(0,0)-bottom left of united states in the ocean, (36,0)-top left near Washington!, (0,30)-bottom right edge of Texas, (36,30) top right near Montana
    filePath = "offshore_MERRA_Format_Bounds.xlsx"
    

    df.to_excel(excel_writer = filePath)