import numpy as np
import pandas as pd
from netCDF4 import Dataset
import seaborn as sns; sns.set()
import matplotlib.pyplot as plt
import os.path
from datetime import datetime

def main(yearList, latLength, longLength, excelFilePath, rawDataFilePath):
    """ Generates IEC wind class map based on 100 meter hub height wind speeds and returns file path written to

    ...

    Args:
    ----------
    `yearList` (list): years for which raw data is available to average wind speeds

    `latLength` (int): amount of unique latitudes in region (for WECC latLength is 37)

    `longLength` (int): amount of unique longitudes in region (for WECC longLength is 31)

    `excelFilePath` (str): file path for where IEC wind class will be written to (default is in same folder as script)

    `rawDataFilePath` (str): file path to where cordDataWestCoastYear or other regions raw data is located 
    (should be only beginning of file name and able to add years to end of str to load in raw data)

    Example:
        rawDataFilePath = 'cordDataWestCoastYear'
        loading data from: cordDataWestCoastYear2016, cordDataWestCoastYear2017...

    Returns:
    ----------
    `filePath` (str): file path that wind power class data is stored, will be different from one passed in if trying to overwrite a file

    """

    windSpeedArrayCul = np.zeros((latLength,longLength))

    #used in calculating hourly wind shear value 
    windScaleValue = np.log(50/10)

    #loading in array of offshore features in dataset will be setting IEC class to level 4 (value is 1 for offshore 0 not)
    offshoreBoundsFilePath = "offshore_MERRA_Format_Bounds.xlsx"
    if not (os.path.isfile(offshoreBoundsFilePath)):
        error_message = 'No offshore MERRA format data, have you run generate_offshore_bounds?'
        raise RuntimeError(error_message)
    else:
        offshoreBounds = pd.read_excel(offshoreBoundsFilePath,index_col=0).values

    #uses values available from 2016-18
    for year in yearList:
        #may need to change file name for location of coord data not included in github due to file size
        fileName = rawDataFilePath + str(year) + ".nc"
        rawData = Dataset(fileName)

        #getting 50 and 10 meter wind speeds in order to extrapolate to 100 meters where IEC values are measured
        eastwardWind50 = rawData.variables["U50M"]
        northwardWind50 = rawData.variables["V50M"]
        eastwardWind10 = rawData.variables["U10M"]
        northwardWind10 = rawData.variables["V10M"]

        latLongIndex = 0
        for lat in range(0,latLength):
            for lon in range(0,longLength):

                #if offshore wind speed subtract negative but later converted to IEC class level 4 for wind yet to be implemented, if not offshore continue
                #with onshore calculations
                if offshoreBounds[lat][lon] == 1:
                    iecLevel = -1
                    windSpeedArrayCul[lat][lon] += iecLevel
                    latLongIndex += 1
                    continue                    
                #combine east and north values to get one single wind speed
                finalWindSpeed50 = np.sqrt((eastwardWind50[latLongIndex][:][:]**2) + (northwardWind50[latLongIndex][:][:]**2))
                finalWindSpeed10 = np.sqrt((eastwardWind10[latLongIndex][:][:]**2) + (northwardWind10[latLongIndex][:][:]**2))
                
                #generating hourly time series for alpha using Time-Averaged Shear Exponent
                wind_sheer = (np.log(finalWindSpeed50/finalWindSpeed10))/windScaleValue
    

                #converting to final wind speed at 100 from 50 meters data measurement
                finalWindSpeed100 = finalWindSpeed50 * (2 ** wind_sheer)

                #papers talk about median giving more accurate estimations
                finalWindSpeed = np.median(finalWindSpeed100)

                #used for assinging iec levels for each year, slow way, could use np.where instead, but easier to understand
                '''
                if finalWindSpeed >= 9:
                    iecLevel = 1
                elif finalWindSpeed >= 8:
                    iecLevel = 2
                elif finalWindSpeed >= 6.5:
                    iecLevel = 3
                elif finalWindSpeed:
                    iecLevel = 0
                '''
                windSpeedArrayCul[lat][lon] += finalWindSpeed
                latLongIndex += 1

    #finding mean for each lat long wind speed value for time period of years
    windSpeedArrayCul = windSpeedArrayCul / len(yearList)

    #values not suitable for wind are assigned 0 value
    windSpeedArrayCul = np.where((windSpeedArrayCul < 6.5) & (windSpeedArrayCul >= 0), 0,windSpeedArrayCul)

    #Wind IEC level 1  anything >= 9 m/s
    windSpeedArrayCul = np.where(windSpeedArrayCul >= 9, 1,windSpeedArrayCul)

    #Wind IEC level 2 8 m/s -> 9 m/s
    windSpeedArrayCul = np.where(windSpeedArrayCul >= 8, 2,windSpeedArrayCul)

    #Wind IEC level 3 6.5 m/s -> 8 m/s
    windSpeedArrayCul = np.where(windSpeedArrayCul >= 6.5, 3,windSpeedArrayCul)

    #Wind level 4 offshore wind yet to be developed
    windSpeedArrayCul = np.where(windSpeedArrayCul < 0, 4,windSpeedArrayCul)


    #transpose to set correct bounds for lat long
    windSpeedArrayCul = windSpeedArrayCul.T

    #test ploting for debugging/visuals
    '''
    ax = sns.heatmap(windSpeedArrayCul)
    plt.ylabel("Long")
    plt.xlabel("Lat")
    plt.title("Average wind speed US (2016-18)")
    plt.show()
    '''
    df = pd.DataFrame(windSpeedArrayCul).T

    #need to enter filepath for writing to excel worksheet, format: rows: 0-36 (lat values) cols: 0 -30 (long values), shape is (37,31)
    #(0,0) bottom left of united states in the ocean, (36,0) top left near Washington!, (0,30) bottom right edge of Texas, (36,30) top right near Montana
    filePath = excelFilePath
    
    #if file path already exists, changes filepath to a new excel worksheet with unique time in format of day_month_year hour_minute_second
    if os.path.isfile(filePath):
        print("Tried overwriting file " + filePath + "\n")
        dt_string = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        filePath = filePath[:-5] + dt_string + ".xlsx"
        print("Instead wrote to " + filePath)

    df.to_excel(excel_writer = filePath)
    return filePath