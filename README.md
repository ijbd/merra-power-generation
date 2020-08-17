PowGen
=====

This program is written to simulate solar and wind power generation at a large scale using the National Renewable Energy Laboratory's System Advisory Model (SAM). Weather data is acquired from NASA's Modern-Era Retrospective analysis for Research and Applications (MERRA) 2 dataset. To approximate Direct Normal Irradiance and Diffuse Horizotal Irradiance from Global Horizontal Irradicatiance for PV simulations, we use the Sandia National Laboratory PVlib Python module. **Note: Some of these instructions are specifically for University of Michigan Researchers, please reach out to ijbd@umich.edu if you have any questions!**


## Download MERRA Data

### 1. Create an [Earth Data Account](https://disc.gsfc.nasa.gov/datasets/M2T1NXRAD_5.12.4/summary?keywords=%22MERRA-2%22) from NASA

### 2. Collect variables from the [Radiation](https://disc.gsfc.nasa.gov/datasets/M2T1NXRAD_5.12.4/summary?keywords=%22MERRA-2%22) (RAD) and [Single-Level](https://disc.gsfc.nasa.gov/datasets/M2T1NXSLV_5.12.4/summary?keywords=%22MERRA-2%22) (SLV) Datasets

- Get a text file that specifies what to download. On the two links above, there is a Subset / Get Data box on the right-hand side. Clicking this will open the different options you can select for the MERRA files. Change the Download Method to  OPeNDAP  and then select the time period, region, and variables. **Make sure the "Use ‘Refine Region’ for geo-spatial submitting" option is checked** or it will not crop the NetCDF file. Set the output format to NetCDF and then hit Get Data. It will require your earth data account. This will generate a text file containing a list of download links for MERRA data with the specified parameters.


#### Required Variables

| Dataset    | Variable Name |
| ----------- | ----------- |
| SLV | 2-meter_air_temperature |
| SLV | 2-meter_eastward_wind |
| SLV | 2-meter_northward_wind |
| SLV | 2-meter_specific_humidity |
| SLV | 10-meter_eastward_wind |
| SLV | 10-meter_northward_wind |
| SLV | eastward_wind_at_50_meters |
| SLV | northward_wind_at_50_meters |
| SLV | surface_pressure |
| RAD | surface_incoming_shortwave_flux |

### 3. Transfer text file with WinSCP to your Great Lakes home directory

Create a directory in the existing MERRA folder for your region:

    mkdir /scratch/mtcraig_root/mtcraig1/shared_data/merraData/resource/<region name>

For consistency, replace `<region name>` with the name of your region in lower case (e.g. "wecc", "ercot").

Create two directories within that folder:

    mkdir /scratch/.../resource/<region name>/raw
    mkdir /scratch/.../resource/<region name>/processed

Copy the MERRA text file into the `raw/` folder from your home directory

    cp <name of text file> /scratch/.../resource/<region name>/raw/

### 4. Download MERRA NetCDF files via command line

Go to the `raw/` folder with the MERRA text file.

    cd /scratch/.../resource/<region name>/raw

Run this command: 

    wget --auth-no-challenge=on --keep-session-cookies --user=<username> --ask-password --content-disposition -i <filename> 

`<username>` is your earth data account username and `<filename>` is the file path and name of the text document (includin .txt at end of file name) from your local position. The wget command can be run from anywhere but I like to run it in the same folder for ease of use letting the `<filename>` only being the filename.txt instead of having to include the file path. You'll be prompted for your earth data password after the command is run and then after inputting your password the download should start for all the NetCDF files in that text document. 

## Process MERRA Data and Simulate Power Generation Profiles

### 1. Download Python Libraries

Assuming you have already downloaded Anaconda and have created/activated a conda environment, the remaining steps require a few python libraries. Download them using the following commands.

    pip install NREL-PySAM
    pip install netCDF4
    pip install pvlib

### 2. Combine raw files into single annual netCDF files:

This script needs to be run for each year individually:

    python /scratch/mtcraig_root/mtcraig1/shared_data/merraData/scripts/rewriteMERRA.py <year> <region>

`<year>` and `<region>` are the year and region of interest, respectively.

e.g.

    python /scratch/.../rewriteMERRA.py 2017 ercot

**Note: This script is currently not included in this repository**

### 3. Generate offshore boundaries with the **generate_boundaries_main** script:

The script calls generate_boundaries which in turns generates a readable excel file in the same format as processed MERRA data using a pre processed offshoreBoundaries netCDF. There is no need to create a shapefile and then convert to readable form for offshore data. Format of excel file: rows: (lat values) cols: (long values)

One can run the script:

    generate_boundaries_main.py

Then it will prompt you in order to enter: min lon, max lon, min lat, and max lat of one's MERRA region, IMPORTANT: one must hit enter (do not enter any value) when prompted to implement state bounds to generate offshore bounds. 

(uses MERRA assumptions of latitude being spaced by .5 and longitude being spaced .625)

(offshoreBoundaries data comes from https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-ocean/)




**Directions for generating single or multi state boundaries:**

Download the respective files at https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2012&layergroup=States+%28and+equivalent%29 and follow the methods of steps two and three at https://disc.gsfc.nasa.gov/information/howto?keywords=state%20by%20state%20data&title=How%20to%20Display%20a%20Shapefile-based%20Data%20Subset%20with%20GrADS to uncompress and create a mask file for each state. (various packages may need to be installed). Changing the resolution of generated netcdfs may also affect the resolution of bounds.

Example command run:

    gdal_rasterize -burn 1 -where STUSPS='STATE ABBREV' -te -180 -50 180 50 -ts 1440 1440 -of netCDF tl_2012_us_state.shp STATEFILENAME.nc

where STATE ABBREV is the states abbreviation, e.g. washington=WA, california=CA, and STATEFILENAME is the soon to be generated netcdf containing region's boundaries.

Once a mask file for each state is generated, place the files in the stateNetcdfs folder (texas_bounds(placeholder).nc is present but should be deleted if texas is not a desired region). Any netcdfs included in this folder will be included in the generation of the main boundaries file.

Run the prior command of **generate_boundaries_main.py** and input the same latitudes and longitudes, but when prompted to **Implement state bounds?** any input (besides enter) will trigger the generation of an excel file named "state_MERRA_Format_Bounds.xlsx" with cells inside the desired region assigned 1 and outside the region 0.


*Example state boundaries netcdfs are located in the folder **exampleStateNetcdfs***

*Script will overwrite any current files if already run prior*
### 4. Generate Capacity Values with the **powGen** script:

This script can be run for single or multiple years.
 
    python /scratch/mtcraig_root/mtcraig1/shared_data/powGen/powGen.py <region> <start year> <end year>

`<region>` is the region of interest. `<start year>` and `<end year>` are the start and end years to run. **Both are inclusive.**

Before submitting the slurm jobs, the powGen script will generate the IEC turbine class map from available wind resources for the region if they do not already exist. This shouldn't take more than 5-10 minutes.

**Note: This script will call one or multiple slurm jobs and will incur a charge**

_______
I'm happy to help in any way I can! Feel free to email me: ijbd@umich.edu

 

