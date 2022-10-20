"""
This scripts concatenates daily MERRA netcdf's into a single netCDF.
"""
import logging
from argparse import ArgumentParser
from pathlib import Path
import pandas as pd
import numpy as np
from netCDF4 import Dataset
from collections import defaultdict
from datetime import datetime
import re

# setup logging
logging.basicConfig(level=logging.DEBUG)

PROJECT_PATH = Path(__file__).parents[1]
MERRA_VARIABLES = [
    'U2M',
    'U10M',
    'U50M',
    'V2M',
    'V10M',
    'V50M',
    'T2M',
    'PS',
    'SWGDN'
]

def get_merra_files_by_date(merra_directory: Path, year: int):
    """Iterate over a directory to find all merra files.
    Results are stored in a dict of lists linking dates to files
    """
    # initialize dict
    merra_files = defaultdict(list)

    # pattern for a merra datetime 'YYYYMMDD' file
    merra_file_pattern = f'MERRA*{year}[0-9][0-9][0-9][0-9].nc4.nc4'

    # iterate through merra files
    for merra_file in merra_directory.glob(merra_file_pattern):
        # get date string
        merra_date_pattern = re.compile(f'{year}[0-9]{{4}}')
        merra_date_str = merra_date_pattern.findall(merra_file.name)[0]

        # convert to datetime
        merra_date = datetime.strptime(merra_date_str, r'%Y%m%d').date()

        # add file
        merra_files[merra_date].append(merra_file)

    return merra_files

def get_merra_dimensions(net_cdf: Path):
    dataset = Dataset(net_cdf)
    lat = dataset.variables['lat'][:]
    lon = dataset.variables['lon'][:]
    return lat, lon

def initialize_dataset(dataset: Dataset, lat: list, lon:list, year:int):
    dataset.createDimension('lat', len(lat))
    dataset.createDimension('lon', len(lon))
    dataset.createDimension('time', 8760)
    dataset.year = year

    # create primary variables
    lat_var = dataset.createVariable('lat', 'double', ('lat'))
    lon_var = dataset.createVariable('lon', 'double', ('lon'))
    lat_var[:] = lat
    lon_var[:] = lon

    # create data variables
    for variable in MERRA_VARIABLES:
        dataset.createVariable(variable, 'double', ('lat', 'lon', 'time'))

def transfer_merra_file(combined_dataset: Dataset, merra_dataset: Dataset, day: int):
    for variable in MERRA_VARIABLES:
        try:
            combined_var = combined_dataset.variables[variable]
            daily_var = merra_dataset.variables[variable]

            reordered_daily = np.transpose(daily_var[:], axes=[1, 2, 0])
            
            start_hour = day*24
            end_hour = (day+1)*24

            combined_var[:, :, start_hour:end_hour] = reordered_daily

            assert(combined_var[0,0,start_hour] == daily_var[0,0,0])
            assert(combined_var[0,0,end_hour-1] == daily_var[-1,0,0])
            assert(combined_var[-1,0,start_hour] == daily_var[0,-1,0])
            assert(combined_var[0,-1,start_hour] == daily_var[0,0,-1])
            assert(combined_var[-1,-1,end_hour-1] == daily_var[-1,-1,-1])
        except KeyError:
            pass

def combine(merra_directory: Path, year: int, output_file: Path):
    logging.info('Starting program...')
    # get merra files from directory
    merra_files = get_merra_files_by_date(merra_directory, year)

    # find variables and dimensions 
    sample_net_cdf = merra_files[datetime(year, 1, 1).date()][0]
    lats, lons = get_merra_dimensions(sample_net_cdf)

    # make directory if necessary
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # write combined file
    with Dataset(output_file, 'w') as combined_dataset:
        initialize_dataset(combined_dataset, lats, lons, year)

        # iterate through dates
        day = 0
        for merra_date in pd.date_range(
            datetime(year, 1, 1),
            datetime(year, 12, 31)
        ):
            # skip leap day
            if merra_date.month == 2 and merra_date.day == 29:
                continue

            # add rad and slv files
            for merra_file in merra_files[merra_date.date()]:
                logging.info(f'Adding file {merra_file}...')
                with Dataset(merra_file) as merra_dataset:
                    transfer_merra_file(combined_dataset, merra_dataset, day)
            day += 1
                
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('merra_directory', type=Path)
    parser.add_argument('year', type=int)

    # get directory and year
    args = parser.parse_args()

    parser.add_argument(
        '--output_file', 
        type=Path,
        default=Path(PROJECT_PATH, 'output', f'combined_merra_{args.year}.nc')
    )

    args = parser.parse_args()

    combine(args.merra_directory, args.year, args.output_file)