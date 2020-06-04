PowGen
=====

This program was written in order to simulate solar and wind power generation at a large scale using the National Renewable Energy Laboratory's System Advisory Model. This program is designed to use weather data acquired from NASA Modern-Era Retrospective analysis for Research and Applications (MERRA) 2 dataset. Using the Sandia National Laboratory PVlib Python module, the MERRA data is processed then run through SAM for wind and solar parameters defined by the user in Power_Generation_.8.py 

How to use:

1. MERRA 2 FILE FORMATTING

The file containing MERRA 2 data needs to be formatted in a particular fashion. (See additional scripts from jflorez)
File should be in netCDf format:

 Dimensions:
  - coordinate (latLong) -- coordinate should be written lat0lon0, lat0lon1, lat0lon2...
  - hour of day (time) size 24
  - day of year (yearDayIndex)

 Variables:
  - from MERRA_2_tavg1_2d_rad_Nx
    - SWGDN
  - from MERRA_2_tavg1_2d_slv_Nx
    - U2M
    - U10M
    - U50M
    - V2M
    - V10M
    - V50M
    - T2M
    - PS 

2. POWER GENERATION PARAMETERS
  - Parameters within powGen_impl.py and powGen.sh should be set by user. 
  - The first set of parameters are in the shell script, powGen.sh. These include year, geographic parameters, and file/folder locations. 
  - System Advisory Model parameters should be set in the respective run_solar and run_wind functions. 

3. COMMAND LINE INSTRUCTION
  - First, change the the shell script permissions to allow execution

    chmod a+rx powGen.sh

  - Then, run the script in the background, while redirecting output to a text file (in this case "black_box.txt")

    nohup bash powGen.sh > black_box.txt&

    
