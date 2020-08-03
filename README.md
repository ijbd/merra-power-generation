PowGen
=====

This program is written to simulate solar and wind power generation at a large scale using the National Renewable Energy Laboratory's System Advisory Model (SAM). Weather data is acquired from NASA's Modern-Era Retrospective analysis for Research and Applications (MERRA) 2 dataset. To approximate Direct Normal Irradiance and Diffuse Horizotal Irradiance from Global Horizontal Irradicatiance for PV simulations, we use the Sandia National Laboratory PVlib Python module. **Note: Some of these instructions are specifically for University of Michigan Researchers, please reach out to ijbd@umich.edu if you have any questions!**


## Download MERRA Data
_________

### 1. Create an [Earth Data Account](https://disc.gsfc.nasa.gov/datasets/M2T1NXRAD_5.12.4/summary?keywords=%22MERRA-2%22) from NASA

### 2. Collect [Radiation Diagnostic](https://disc.gsfc.nasa.gov/datasets/M2T1NXRAD_5.12.4/summary?keywords=%22MERRA-2%22) (RAD) and [Single-Level Diagnostic](https://disc.gsfc.nasa.gov/datasets/M2T1NXSLV_5.12.4/summary?keywords=%22MERRA-2%22) (SLV) Data

> Get a text file that specifies what to download. On the two links above, there is a Subset / Get Data box on the right-hand side. Clicking this will open the different options you can select for the MERRA files. Change the Download Method to  OPeNDAP  and then select the time period, region, and variables. **Make sure the  "Use ‘Refine Region’ for geo-spatial submitting" option is checked** or it will not crop the NetCDF file. Set the output format to NetCDF and then hit Get Data. It will then require an earth data account for you to download the text document containing each NetCDF file in it with the specified parameters.
>
> #### Required Variables
> From SLV (link above): 
> - 2-meter_air_temperature
> - 2-meter_eastward_wind
> - 2-meter_northward_wind
> - 2-meter_specific_humidity
> - 10-meter_eastward_wind
> - 10-meter_northward_wind
> - eastward_wind_at_50_meters
> - northward_wind_at_50_meters 
> - surface_pressure
> 
> From RAD (link above):
> - surface_incoming_shortwave_flux

### 3. Transfer text files over by WinSCP to your Great Lakes home directory

> Create a directory in the existing MERRA folder for your region:
>
> `mkdir /scratch/mtcraig_root/mtcraig1/shared_data/merraData/resource/<region name>`
>
> For consistency, replace `<region name>` with the name of your region in lower case (e.g. "wecc", "ercot").
>
> Create two directories within that folder:
>
> `mkdir /scratch/.../resource/<region name>/raw`
>
> `mkdir /scratch/.../resource/<region name>/processed`
>
> Copy the MERRA text file into the `raw` folder from your home directory
>
> `cp <name of text file> /scratch/.../resource/<region name>/raw/`

### 4. Download MERRA NetCDF files via command line

> Go to the `raw` folder with the MERRA text file.
>
> `cd /scratch/.../resource/<region name>/raw`
>
> Run this command: 
>
> `wget --auth-no-challenge=on --keep-session-cookies --user=<username> --ask-password --content-disposition -i <filename>`   
>
>`<username>` is your earth data account username and `<filename>` is the file path and name of the text document (includin .txt at end of file name) from your local position. The wget command can be run from anywhere but I like to run it in the same folder for ease of use letting the `<filename>` only being the filename.txt instead of having to include the file path. You'll be prompted for your earth data password after the command is run and then after inputting your password the download should start for all the NetCDF files in that text document. 

## Process MERRA Data and Generate Power Generation Profiles
____________________

### 1. Combine raw files into single annual netCDF files:

> This script needs to be run for each year individually:
>
> `python /scratch/mtcraig_root/mtcraig1/shared_data/merraData/scripts/rewriteMERRA.py <year> <region>` 
>
>`<year>` and `<region>` are the year and region of interest, respectively.
>
> e.g.
>
> `python /scratch/.../rewriteMERRA.py 2017 ercot`
>
> **Note: This script is currently not included in this repository**

### 2. Generate Capacity Values with the **powGen** script:

> This script can be run for single or multiple years.
> 
> `python /scratch/mtcraig_root/mtcraig1/shared_data/powGen/powGen.py <region> <start year> <end year>`
>
> `<region>` is the region of interest. `<start year>` and `<end year>` are the start and end years to run. **Both are inclusive.**
>
> Before submitting the slurm jobs, the powGen script will generate the IEC turbine class map from available wind resources for the region if they do not already exist. This shouldn't take more than 5-10 minutes.
>
>**Note: This script will call one or multiple slurm jobs and will incur a charge**

_______
I'm happy to help in any way I can! Feel free to email me: ijbd@umich.edu

 

