#!/usr/bin/env python
# coding: utf-8

import numpy as np
import os, sys, datetime
from netCDF4 import Dataset
import csv
import math
import PySAM.Pvwattsv7 as pv
import pandas as pd
import pvlib
import PySAM.Windpower as wp
import os.path
from os import path

#SYSTEM INPUTS
year = int(sys.argv[1])
region = sys.argv[2]
print('Year, Region: '+str(year)+' '+region,flush=True)


def get_lat_lon(processed_merra_file):
    
    data = Dataset(processed_merra_file)
    lats = np.array(data.variables['lat'][:3])
    lons = np.array(data.variables['lon'][:3])
    data.close()    
    num_lats = lats.size
    num_lons = lons.size
    return lats, lons, num_lats, num_lons


def get_power_curve(power_curve_file):
    power_curve = dict()
    power_curve["speed"] = np.array(pd.read_csv(power_curve_file, skiprows=0, usecols=[0]).values)
    power_curve["powerout"] = np.array(pd.read_csv(power_curve_file, skiprows=0, usecols=[1]).values)
    return power_curve


def create_netCDF_files(year, lats, lons, destination):
    solar_name = destination + str(year) + "_solar_generation_cf.nc"
    solar = Dataset(solar_name, "w")
    lat = solar.createDimension("lat",lats.size)
    lon = solar.createDimension("lon",lons.size)
    hour = solar.createDimension("hour", 8760)
    solar_cf = solar.createVariable("cf","f4",("lat","lon","hour",))
    latitude = solar.createVariable("lat", "f4",("lat",))
    longitude = solar.createVariable("lon", "f4",("lon",))
    latitude[:] = lats
    longitude[:] = lons
    solar.close()
    
    
    wind_name = destination + str(year) + "_wind_generation_cf.nc"
    wind = Dataset(wind_name, "w")
    lat = wind.createDimension("lat",lats.size)
    lon = wind.createDimension("lon",lons.size)
    hour = wind.createDimension("hour", 8760)
    wind_cf = wind.createVariable("cf","f4",("lat","lon","hour",))
    latitude = solar.createVariable("lat", "f4",("lat",))
    longitude = solar.createVariable("lon", "f4",("lon",))
    latitude[:] = lats
    longitude[:] = lons
    wind.close()
    return 0


def create_csv(year, latitude, longitude): #lat lon in degrees
    solar_csv = str(year) + '_' + str(latitude) + '_' + str(longitude) + '.csv'
    with open(solar_csv, 'w', newline='') as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(['Latitude']+['Longitude']+['Time Zone']+['Elevation'])
        csvWriter.writerow([latitude]+[longitude]+[0]+[500])
        csvWriter.writerow(['Year']+['Month']+['Day']+['Hour']+['DNI']+['DHI']+['Wind Speed']+['Temperature'])
        csvfile.close()
    return solar_csv


def create_srw(year, latitude, longitude): #lat lon in degrees
    wind_srw = str(year) + '_' + str(latitude) + '_' + str(longitude) + '_wp.srw'
    with open(wind_srw, 'w', newline='') as csvfile:
        csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvWriter.writerow(['loc id=?']+['city=?']+['state=?']+['country=?']+[year]+[latitude]+[longitude]+['elevation=?']+[1]+[8760])
        csvWriter.writerow(['SAM wind power resource file'])
        csvWriter.writerow(['Temperature']+['Pressure']+['Speed']+['Speed']+['Speed']+['Direction'])
        csvWriter.writerow(['C']+['atm']+['m/s']+['m/s']+['m/s']+['degrees'])
        csvWriter.writerow(['2']+['2']+['2']+['10']+['50']+['50'])
        csvfile.close()
    return wind_srw

# SKIPS LEAP DAYS
def get_date(jd): 
    daysInMonth = [0,31,59,90,120,151,181,212,243,273,304,334]
    for i in range(12):
        if jd > daysInMonth[i]:
            month = i + 1
    if jd > 31:
        day = jd % daysInMonth[month-1]
    else:
        day = jd
    return month, day      


def get_data(latitude, longitude, num_lons, merra_data):
    
    latLon = latitude * num_lons + longitude # Processed data comes in vector form
    
    ghi = np.squeeze(np.array(merra_data.variables['SWGDN'][latLon, :, :]))
    ghi = ghi.reshape(ghi.size)
    v10m = np.squeeze(np.array(merra_data.variables['V10M'][latLon, :, :]))
    v10m = v10m.reshape(v10m.size)
    u2m = np.squeeze(np.array(merra_data.variables['U2M'][latLon, :, :]))
    u2m =u2m.reshape(u2m.size)
    v2m = np.squeeze(np.array(merra_data.variables['V2M'][latLon, :, :]))
    v2m = v2m.reshape(v2m.size)
    u10m = np.squeeze(np.array(merra_data.variables['U10M'][latLon, :, :]))
    u10m = u10m.reshape(u10m.size)
    v10m = np.squeeze(np.array(merra_data.variables['V10M'][latLon, :, :]))
    v10m = v10m.reshape(v10m.size)
    u50m = np.squeeze(np.array(merra_data.variables['U50M'][latLon, :, :]))
    u50m = u50m.reshape(u50m.size)
    v50m = np.squeeze(np.array(merra_data.variables['V50M'][latLon, :, :]))
    v50m = v50m.reshape(v50m.size)
    t2m = np.squeeze(np.array(merra_data.variables['T2M'][latLon, :, :]))
    t2m = t2m.reshape(t2m.size)
    pressure_Pa = np.squeeze(np.array(merra_data.variables['PS'][latLon, :, :]))
    pressure_Pa = pressure_Pa.reshape(pressure_Pa.size)
    
    pressure = pressure_Pa / 101325.0
    windSpeed2 = (v2m**2 + u2m**2)**.5
    windSpeed10 = (v10m**2 + u10m**2)**.5
    windSpeed50 = (v50m**2 + u50m**2)**.5
    windDirection = get_windDirection(u50m, v50m)
    temperature = (t2m - 273.15)
    
    return ghi, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection 


def get_windDirection(u50m, v50m):
    
    direction = np.zeros(u50m.size)
    eastward = np.logical_and(u50m > 0, v50m != 0) 
    westward = np.logical_and(u50m < 0, v50m != 0)
    pure_northward = np.logical_and(u50m == 0, v50m > 0)
    pure_southward = np.logical_and(u50m == 0, v50m < 0)
    pure_eastward = np.logical_and(u50m > 0, v50m == 0)
    pure_westward = np.logical_and(u50m < 0, v50m == 0)
    direction[westward] = 90 - np.arctan(v50m[westward] / u50m[westward]) / np.pi * 180.
    direction[eastward] = 270 - np.arctan(v50m[eastward] / u50m[eastward]) / np.pi * 180.
    direction[pure_northward] = 180
    direction[pure_southward] = 0
    direction[pure_eastward] = 270
    direction[pure_westward] = 90

    return direction


def get_date_time_index(year, month, day):
    if day < 10:
        two_dig_day = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09']
        str_day = two_dig_day[day]
    else:
        str_day = str(day)
    if month < 10:
        two_dig_month = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09']
        str_month = two_dig_month[month]
    else:
        str_month = str(month)
    times = pd.date_range(str(year)+'-'+str_month+'-'+str_day, periods=24, freq='H')
    return times


# PVLIB from Sandia National Laboratory to estimate dni/dhi from ghi using DISC model
def get_dni_dhi(year, jd, month, day, latitude, longitude, ghi):
    latitude_rads = latitude * 3.14159 / 180.0
    times = get_date_time_index(year, month, day)
    eqt = pvlib.solarposition.equation_of_time_pvcdrom(jd) # find 'equation of time' of given day (in minutes) 
    dec_rads = pvlib.solarposition.declination_spencer71(jd) # find 'solar declination' of given day (in radians)
    dec = dec_rads * 180. / np.pi # convert 'solar declination' (degrees)
    ha = np.array(pvlib.solarposition.hour_angle(times, longitude, eqt)) # find array of 'hour angles' for given day (in degrees)
    ha_rads = ha * np.pi / 180. # convert 'hour angle' (degrees)
    zen_rads = np.array(pvlib.solarposition.solar_zenith_analytical(latitude_rads, ha_rads, dec_rads)) # find array of 'zenith angles' for given day (in radians)
    zen = zen_rads * 180. / np.pi # convert 'zenith angles' (degrees)
    dni_temp = pvlib.irradiance.dirint(ghi, zen, times, pressure=None, use_delta_kt_prime=True, temp_dew=None, min_cos_zenith=0.0, max_zenith=90) #CHANGE
    dni = np.array(dni_temp.fillna(0)) #CHANGE
    dhi = ghi - dni * np.cos(zen_rads)
    return dni, dhi


def write_day2csv(solar_csv, year, month, day, dni, dhi, windSpeed, temperature):
    with open(solar_csv, 'a', newline='') as csvfile:
        for i in range(24):
            csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvWriter.writerow([year]+[month]+[day]+[i]+[dni[i]]+[dhi[i]]+[windSpeed[i]]+[temperature[i]])
        csvfile.flush()
        csvfile.close()


def write_2srw(wind_srw, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection):
    with open(wind_srw, 'a', newline='') as csvfile:
        for i in range(temperature.size):
            csvWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvWriter.writerow([temperature[i]]+[pressure[i]]+[windSpeed2[i]]+[windSpeed10[i]]+[windSpeed50[i]]+[windDirection[i]])
        csvfile.flush()
        csvfile.close()


def run_solar(solar_csv, latitude):
    s = pv.default("PVWattsNone")
    
    ##### Parameters #######
    s.SolarResource.solar_resource_file = solar_csv
    s.SystemDesign.array_type = 0
    s.SystemDesign.azimuth = 180
    s.SystemDesign.tilt = abs(latitude)
    nameplate_capacity = 1000 #kw
    s.SystemDesign.system_capacity = nameplate_capacity   # System Capacity (kW)
    s.SystemDesign.dc_ac_ratio = 1.1 #DC to AC ratio
    s.SystemDesign.inv_eff = 96 #default inverter eff @ rated power (%)
    s.SystemDesign.losses = 14 #other DC losses (%) (14% is default from documentation)
    ########################
    
    s.execute()
    output_cf = np.array(s.Outputs.ac) / (nameplate_capacity * 1000) #convert AC generation (w) to capacity factor
    
    return output_cf


def run_wp(wind_srw, power_curve):
    d = wp.default("WindPowerNone")
    
    ##### Parameters #######
    ##### based on the Mitsubishi MWT 1000A ######
    d.Resource.wind_resource_filename = wind_srw
    d.Resource.wind_resource_model_choice = 0
    d.Turbine.wind_turbine_powercurve_powerout = power_curve["powerout"]
    d.Turbine.wind_turbine_powercurve_windspeeds = power_curve["speed"]
    d.Turbine.wind_turbine_rotor_diameter = 61.4
    d.Turbine.wind_turbine_hub_ht = 80
    nameplate_capacity = 1000 #kw
    d.Farm.system_capacity = nameplate_capacity # System Capacity (kW)
    d.Farm.wind_farm_wake_model = 0
    d.Farm.wind_farm_xCoordinates = np.array([0]) # Lone turbine (centered at position 0,0 in farm)
    d.Farm.wind_farm_yCoordinates = np.array([0])
    ########################
    
    d.execute()
    output_cf = np.array(d.Outputs.gen) / nameplate_capacity #convert AC generation (kw) to capacity factor
    
    return output_cf


def write_cord(year, solar_outputs, wind_outputs, lat, lon, destination):
    solar_name = destination + str(year) + "_solar_generation_cf.nc"
    solar = Dataset(solar_name, "a")
    solar_cf = solar.variables['cf']
    solar_cf[lat, lon, :] = solar_outputs
    solar.close()
    
    wind_name = destination + str(year) + "_wind_generation_cf.nc"
    wind = Dataset(wind_name, "a")
    wind_cf = wind.variables['cf']
    wind_cf[lat, lon, :] = wind_outputs
    wind.close()
    return 0


def main(year,region):
        
    print('Begin Program: \t {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
    
    processed_merra_path = '/scratch/mtcraig_root/mtcraig1/shared_data/merraData/resource/'+region+'/processed/'
    if region == "wecc": processed_merra_name = 'cordDataWestCoastYear'+str(year)+'.nc'
    else: processed_merra_name = 'processedMERRA'+region+str(year)+'.nc'
    processed_merra_file = processed_merra_path + processed_merra_name
    destination_file_path = '/scratch/mtcraig_root/mtcraig1/shared_data/merraData/cfs/'+region+'/'

    #get latitude and longitude arrays
    lat, lon, num_lats, num_lons = get_lat_lon(processed_merra_file)

    #check if output files exist
    create_netCDF_files(year, lat, lon, destination_file_path)

    #get power curve for wind
    power_curve_file = './sample_power_curve.csv'
    power_curve = get_power_curve(power_curve_file)

    #simulate power generation for every latitude and longitude
    for longitude in range(lon.size):
        for latitude in range(lat.size):
            solar_csv = create_csv(year, lat[latitude], lon[longitude])
            wind_srw = create_srw(year, lat[latitude], lon[longitude])
            
            merra_data = Dataset(processed_merra_file)
            ghi, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection = get_data(latitude, longitude, num_lons, merra_data)
            merra_data.close()
            
            # write wind resource data to srw for SAM
            write_2srw(wind_srw, temperature, pressure, windSpeed2, windSpeed10, windSpeed50, windDirection)

            # approximate dni, dhi, then write solar resource data to csv for SAM
            for jd in range(int(ghi.size / 24)):
                month, day = get_date(jd + 1)
                dni, dhi = get_dni_dhi(year, jd + 1, month, day, lat[latitude], lon[longitude], ghi[(jd)*24:(jd+1)*24]) #disc model
                write_day2csv(solar_csv, year, month, day, dni, dhi, windSpeed2[(jd)*24:(jd+1)*24], temperature[(jd)*24:(jd+1)*24])
            
            # simulate generation with System Advisory Model
            solar_outputs = run_solar(solar_csv, lat[latitude])
            wind_outputs = run_wp(wind_srw, power_curve)
            
            # remove resource data (save space)
            os.remove(solar_csv)
            os.remove(wind_srw)

            # write capacity factors for coordinate in netcdf
            write_cord(year, solar_outputs, wind_outputs, latitude, longitude, destination_file_path)

            # status update
            print("%f, " %lat[latitude], "%f\t" %lon[longitude], '{:%Y-%m-%d %H:%M:%S} \n'.format(datetime.datetime.now()))
        print('Longitude finished: \t {:%Y-%m-%d %H:%M:%S} \n'.format(datetime.datetime.now()))

main(year,region)

