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
  
    This command downloads every file in the download link text document. This can take several hours depending on the scale of your geography

### 6. Setup Python environment

- Create a new python environment in this directory.

    `python -m venv env`

- Install dependent libraries

    `python -m pip install -r requirements.txt`
  

### 7. Combine daily MERRA data into annual dataset

    `python src/combine_merra.py <merra_directory> <year>`

### 8. Simulate power generation using `power_generation.py`

    `python src/power_generation.py <combined_merra_file> <output_file>`

## Warning

As of September 29th, 2022, several major changes were made to this repository:

1. Removed hard-coded variables and file locations for UMICH researchers.
   
2. Use Python standard library where possible for clarity.
   
3. Document environment and update external libraries.

4. *Switched wind class assignment to single year.

5. *Removed masks for state and offshore boundaries.

The reason for rewriting large portions of this repository was to make it more portable and readable.

**\*Features have not been fully re-integrated, but that does not mean they cannot or should not be.**

To see how these features were previously implemented, see commit      

    379f57034726e9a8439a37e37a83d520ef99ba66

_______

I'm happy to help in any way I can! Feel free reach out: ijbd@umich.edu

