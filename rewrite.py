import sys,os
import numpy as np
import time as stopWatch
from netCDF4 import Dataset
from datetime import date, timedelta
from collections import defaultdict

#TAKE INPUTS FROM SHELL SCRIPT
#Process inputs and call master function
inputData = sys.argv[1:] #exclude 1st item (script name)
year = int(inputData[0])
powSys = str(inputData[1]) #wecc or ercot
print('Running year:' + str(year) + ' and system: ' + powSys,flush=True)

#DEFINE PARAMETERS
#start & end dates for dataset
start_date = date(year, 1, 1)
end_date = date(year, 12, 31)
#Setup for loading the data through each day by day dataset FILE NAME for the two different MERRA files
merraRoot = str("/scratch/mtcraig_root/mtcraig1/shared_data/merraData/resource/" + powSys)
rawDir = os.path.join(merraRoot,'raw')
if year <= 2010:
    baseWord1 = os.path.join(rawDir,"MERRA2_300.tavg1_2d_slv_Nx.")#for slv data
    baseWord2 = os.path.join(rawDir,"MERRA2_300.tavg1_2d_rad_Nx.")#for rad data
if year > 2010:
    baseWord1 = os.path.join(rawDir,"MERRA2_400.tavg1_2d_slv_Nx.")
    baseWord2 = os.path.join(rawDir,"MERRA2_400.tavg1_2d_rad_Nx.")
#Directory in which to store files
processDir = os.path.join(merraRoot,'processed')
fileName = os.path.join(processDir,"processedMERRA" + powSys + str(year) + ".nc")

#method to save each coordinate in its own file with its own variables
def rewriteData(data1, variableTag):
    data = np.zeros((len(data1.variables[variableTag]),(len(data1.variables[variableTag][0])*len(data1.variables[variableTag][0][0]))))
    timeValueIndex = -1
    latLongIndex = 0
    for time in data1.variables[variableTag]:
        timeValueIndex += 1
        latLongIndex = 0
        for lat in time:
            for long in lat:
                data[timeValueIndex][latLongIndex] = long
                latLongIndex += 1
    return data

#timestep leave at 1 day
delta = timedelta(days=1)

#Creating datsets for all the different variables
masterDataset = defaultdict(list)

daysPassed = 0
previousYear = start_date.year

#stop watch to see how long certain program parts take
start_timeExtract = stopWatch.time()
start_timeToal = stopWatch.time()

# ***************** IJBD EDIT (PASS LAT/LONS) ***************** #
date = start_date.strftime("%Y%m%d")
filename = baseWord1 + date + ".SUB.nc" #.nc4.nc4
data = Dataset(filename)
lats = np.array(data.variables['lat'][:])
lons = np.array(data.variables['lon'][:])
data.close()
# ************************************************************* #

#main loop to iterate through the different day netcdf files
while start_date <= end_date:

    #checking for leap day then incremanting to the next day (skipping it) if it is a leap day
    if(start_date.year % 4 == 0 and start_date.month == 2 and start_date.day == 29):
        start_date += delta

    date = start_date.strftime("%Y%m%d")
    filename1 = baseWord1 + date + ".SUB.nc" #.nc4.nc4
    filename2 = baseWord2 + date + ".SUB.nc" # .nc4.nc4

    data1 = Dataset(filename1)
    data2 = Dataset(filename2)

    #adding new data from netcdf day files to specific lat long cords

    #Eastward winds at 2,10, and 50 meters
    masterDataset["U2M"].append(rewriteData(data1,"U2M"))
    masterDataset["U10M"].append(rewriteData(data1,"U10M"))
    masterDataset["U50M"].append(rewriteData(data1,"U50M"))

    #Northward winds at 2,10, and 50 meters   
    masterDataset["V2M"].append(rewriteData(data1,"V2M"))
    masterDataset["V10M"].append(rewriteData(data1,"V10M"))
    masterDataset["V50M"].append(rewriteData(data1,"V50M"))

    #Surface Temperature at 2 meters   
    masterDataset["T2M"].append(rewriteData(data1,"T2M"))

    #Surface Pressure
    masterDataset["PS"].append(rewriteData(data1,"PS"))

    #Specific humidity 
    masterDataset["QV2M"].append(rewriteData(data1,"QV2M"))

    #surface_incoming_shortwave_flux
    masterDataset["SWGDN"].append(rewriteData(data2,"SWGDN"))

    data1.close()
    data2.close()

    #Removing day files after unloading the data into specific cords, optional may speed up runtime
    #os.remove(filename)
    #os.remove(filename2)
    daysPassed += 1
    start_date += delta
timeLevel = 0

#calculating extracting data length time
extractTimeLength = (stopWatch.time() - start_timeExtract)
start_timeRewrite = stopWatch.time()

print("Finished extracting data sets from " + str(daysPassed) + " days!")
print("It took " + str(round(extractTimeLength,2))  + " seconds to extract the data.")
print("Now writing lat and long specific files!")

#writing new netcdf format into file, change name and location
newNetCDF = Dataset(fileName, 'w')
print("netCDF file opened for writing the processed data")

#declaring dimensions: goes lat, long,  year-1980-2019, day 0-365, time 0-24
newNetCDF.createDimension('yearDayIndex',len(masterDataset["U2M"]))
newNetCDF.createDimension('time', len(masterDataset["U2M"][0]))
newNetCDF.createDimension('latLong',len(masterDataset["U2M"][0][0]))

print("Dimensions are declared as yearDayIndex, time, and product of latlong size")
# ************** IJBD EDITS (PASS LAT/LONS) *************** #

print("Writing Lat and Lon variables in the new netCDF4 file, and assigning data")
newNetCDF.createDimension('lat',len(lats))
newNetCDF.createDimension('lon',len(lons))
varlat = newNetCDF.createVariable("lat",'double', ("lat",))
varlon = newNetCDF.createVariable("lon",'double', ("lon",))
varlat[:] = lats
varlon[:] = lons

print("Lat and Lon variables in the new netCDF4 file have been created")
# ********************************************************* #

#Setting up the 10 different variables, goes latLong 0-4700, yearDay 0-daysPassed, time 0-24

print("Setting up the datatype for 10 variables - U2M, U10M< U50M< V2M, T2M, QV2M, PS, and SWGDN")

varU2M = newNetCDF.createVariable("U2M",'double', ('latLong','yearDayIndex','time'))
varU10M = newNetCDF.createVariable("U10M",'double', ('latLong','yearDayIndex','time'))
varU50M = newNetCDF.createVariable("U50M",'double', ('latLong','yearDayIndex','time'))
varV2M = newNetCDF.createVariable("V2M",'double', ('latLong','yearDayIndex','time'))
varV10M = newNetCDF.createVariable("V10M",'double', ('latLong','yearDayIndex','time'))
varV50M = newNetCDF.createVariable("V50M",'double', ('latLong','yearDayIndex','time'))
varT2M = newNetCDF.createVariable("T2M",'double', ('latLong','yearDayIndex','time'))
varQV2M = newNetCDF.createVariable("QV2M",'double', ('latLong','yearDayIndex','time'))
varPS= newNetCDF.createVariable("PS",'double', ('latLong','yearDayIndex','time'))
varSWGDN = newNetCDF.createVariable("SWGDN",'double', ('latLong','yearDayIndex','time'))

print("Data types have been assigned")

#loop for writing out cord file

print("starting while loop")
latLongIndex = 0
while latLongIndex < len(masterDataset["U2M"][0][0]):
    yearDayIndex = 0
    date = 0
    while yearDayIndex < len(masterDataset["U2M"]): #get each day from the master list
            timeLevel = 0
            while timeLevel < len(masterDataset["U2M"][0]):
                varU2M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["U2M"][yearDayIndex][timeLevel][latLongIndex]
                varU10M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["U10M"][yearDayIndex][timeLevel][latLongIndex]
                varU50M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["U50M"][yearDayIndex][timeLevel][latLongIndex]
                varV2M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["V2M"][yearDayIndex][timeLevel][latLongIndex]
                varV10M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["V10M"][yearDayIndex][timeLevel][latLongIndex]
                varV50M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["V50M"][yearDayIndex][timeLevel][latLongIndex]
                varT2M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["T2M"][yearDayIndex][timeLevel][latLongIndex]
                varQV2M[latLongIndex,yearDayIndex,timeLevel] = masterDataset["QV2M"][yearDayIndex][timeLevel][latLongIndex]
                varPS[latLongIndex,yearDayIndex,timeLevel] = masterDataset["PS"][yearDayIndex][timeLevel][latLongIndex]
                varSWGDN[latLongIndex,yearDayIndex,timeLevel] = masterDataset["SWGDN"][yearDayIndex][timeLevel][latLongIndex]
                timeLevel+= 1
            yearDayIndex+= 1
    latLongIndex += 1

#Runtime for program
rewriteTimeLength = (stopWatch.time() - start_timeRewrite)
totalTimeLength = (stopWatch.time() - start_timeToal)
print("It took " + str(round(rewriteTimeLength,2))  + " seconds to rewrite older datasets!")#time to rewrite datsets and delete old files
print("It took " + str(round(totalTimeLength,2))  + " seconds to execute the whole program!")#total time for program to run

print("Finished while loop; data has beeen processed")
