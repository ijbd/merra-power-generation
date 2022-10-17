MERRA Power Generation
=====

This program uses NREL's System Advisor Model ([SAM](https://sam.nrel.gov/software-development-kit-sdk/pysam.html)) to estimate hourly solar and wind capacity factors. We use meteorological data from NASA Modern-Era Retrospective analysis for Research and Applications (MERRA) 2 dataset. Capacity factors are saved in [NetCDF](https://www.unidata.ucar.edu/software/netcdf/) file format. 


## Instructions

### 1. Clone this repository

    git clone https://github.com/ijbd/merra-power-generation

### 2. Create a [NASA Earth Data Account](https://urs.earthdata.nasa.gov/users/new)

### 3. Collect variables from the [MERRA Radiation](https://disc.gsfc.nasa.gov/datasets/M2T1NXRAD_5.12.4/summary?keywords=%22MERRA-2%22) (RAD) dataset

- Click **Subset / Get Data** on the right-hand side of the link above
- Expand **Download Method**, select *OPeNDAP*
- Expand **Refine Date Range**, include a whole year
- Expand **Refine Region**, select according to your research needs. 
- **Make sure to check the "Use ‘Refine Region’ for geo-spatial submitting" option**
- Expand **Variables**, select variables according to [Table 1](#table-1-required-variables) 
- Expand **File Format**, select *netCDF*
- Click **Get Data**
  
    This will generate a text file containing a list of download links. In step 5, we will use this file to download daily MERRA data

### 4. Collect variables from the [MERRA Single-Level](https://disc.gsfc.nasa.gov/datasets/M2T1NXSLV_5.12.4/summary?keywords=%22MERRA-2%22) (SLV) dataset

- Repeat the description in step 2 for the link above, using the variables in [Table 1](#table-1-required-variables) for the *RAD* dataset
- **Make sure the selected Date Range and Region are consistent between steps 2 and 3**

#### **Table 1:** Required Variables

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

### 5. Download daily MERRA files

- Create a download destination directory. This can be anywhere, and it will hold all of the MERRA data. We recommend creating a new folder called `merra` within the `input` folder of this repository.
- Copy the download link files from steps 2 and 3 into the download destination directory
- Download the files into the download destination directory using `wget` or a similar tool

      wget --auth-no-challenge=on --keep-session-cookies --user=\<username\>--ask-password --content-disposition -i \<filename\>

  - `<username>` is your earth data account username
  - `<filename>` is the file path and name of the download link text document (including .txt at end of file name)
  - You will be prompted for your earth data password
  
    This command downloads every file in the download link text document. It will take about one hour for a year of data, but you should see progress every minute or so

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

Then it will prompt you in order to enter: min lon, max lon, min lat, and max lat of one's MERRA region, and "Implement State Bounds? (y/n): ", if the goal is for implementing offshore turbines type 'n' (y option is for future development)

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

This data output of this repository were restructured on September 29th, 2022. For previous versions, see commit 379f57034726e9a8439a37e37a83d520ef99ba66

_______
I'm happy to help in any way I can! Feel free to email me: ijbd@umich.edu

 

