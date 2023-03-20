from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import List
import logging
import math
import csv
from datetime import datetime, timedelta

from netCDF4 import Dataset
import numpy as np
import pandas as pd
import pvlib
import PySAM.Pvwattsv8 as pv
import PySAM.Windpower as wp

# setup logging
logging.basicConfig(level=logging.DEBUG)

PROJECT_PATH = Path(__file__).parents[1]
HOURS_PER_YEAR = 24*365
ATM_PER_PASCAL = 1 / 101325
KELV_CELSIUS_OFFSET = 273.15
NETCDF_FILL_VALUE = 9.83e31


class MerraPowerGeneration:
    def __init__(
        self, 
        combined_merra_file: Path, 
        output_file: Path,
        wind_power_curve_file: Path,
        mask_files: List[Path]=None
    ):
        self.combined_merra_file = combined_merra_file
        self.output_file = output_file
        self.wind_power_curve_file = wind_power_curve_file
        self.mask_files = mask_files

        self._load_merra_data()
        self._process_merra_data()
        self._load_power_curves()
        self._load_masks()

    def _load_merra_data(self):
        """Open MERRA data from netCDF."""
        logging.info(f'Loading MERRA data from {self.combined_merra_file}...')
        with Dataset(self.combined_merra_file) as dataset:
            self.year = dataset.year
            self.variables = {name : np.array(var[:]) for name, var in dataset.variables.items()}

    @staticmethod
    def _fill_masked_val(arr: np.ndarray, fill_val: float):
        return np.where(
            arr > NETCDF_FILL_VALUE,
            fill_val,
            arr
        )

    @staticmethod
    def _get_wind_direction(eastward_velocity, northward_velocity):
        """Find wind travel direction (degrees from due south)"""
        # get cases
        eastward = np.logical_and(
            eastward_velocity > 0,
            northward_velocity != 0
        ) 
        westward = np.logical_and(
            eastward_velocity < 0,
            northward_velocity != 0
        )
        pure_northward = np.logical_and(
            eastward_velocity == 0,
            northward_velocity > 0
        )
        pure_southward = np.logical_and(
            eastward_velocity == 0,
            northward_velocity < 0
        )
        pure_eastward = np.logical_and(
            eastward_velocity > 0,
            northward_velocity == 0
        )
        pure_westward = np.logical_and(
            eastward_velocity < 0,
            northward_velocity == 0
        )

        # get direction matrix
        direction = np.zeros(eastward_velocity.shape)

        direction[westward] = 90 - np.arctan(northward_velocity[westward] / eastward_velocity[westward]) / np.pi * 180.
        direction[eastward] = 270 - np.arctan(northward_velocity[eastward] / eastward_velocity[eastward]) / np.pi * 180.
        direction[pure_northward] = 180
        direction[pure_southward] = 0
        direction[pure_eastward] = 270
        direction[pure_westward] = 90

        return direction

    @staticmethod
    def scale_wind_height(
        height_1,
        wind_speed_height_1,
        height_2,
        wind_speed_height_2,
        height_3
    ):
        """Wind profile power law"""
        wind_sheer = np.where(
            np.logical_and(wind_speed_height_1 > 0.1, wind_speed_height_2 > 0.1),
            np.log(wind_speed_height_2 / wind_speed_height_1) / math.log(height_2 / height_1),
            0
        )
        wind_speed_height_3 = wind_speed_height_2 \
            * (height_3 / height_2) \
            ** wind_sheer

        return wind_speed_height_3

    @staticmethod
    def _get_wind_turbine_class(wind_speed_10, wind_speed_50):
        """Estimate the IEC wind turbine class based on
        median wind speed.
        """
        # approximate wind speed at 100 m
        wind_speed_100 = MerraPowerGeneration.scale_wind_height(
            10,
            wind_speed_10,
            50,
            wind_speed_50,
            100
        )

        # evaluate wind turbine class by annual median wind speed
        median_wind_speed = np.median(wind_speed_100, axis=2)

        # classify wind turbine class by median wind speed.
        # In order of slowest to fastest wind speeds, 
        # turbines are assigned classes 3, 2, and 1, respectively.
        wind_turbine_class = np.where(median_wind_speed >= 8, 2, 3)
        wind_turbine_class = np.where(median_wind_speed >= 9, 1, wind_turbine_class)

        return wind_turbine_class
        
    def _process_merra_data(self):
        """Convert units, fill masked values and rename variables."""
        logging.info(f'Converting MERRA variables...')
        # pressure in atmospheres
        self.variables['pressure_atm'] = (self.variables['PS'] * ATM_PER_PASCAL)
        self.variables['pressure_atm'] = self._fill_masked_val(
            self.variables['pressure_atm'],
            1.0
        )

        # temperature in C
        self.variables['temperature_c'] = self.variables['T2M'] - KELV_CELSIUS_OFFSET
        self.variables['temperature_c'] = self._fill_masked_val(
            self.variables['temperature_c'],
            0.0
        )

        # wind speed
        for height in [2, 10, 50]:
            # wind speed
            self.variables[f'wind_speed_{height}_m_per_s'] = np.sqrt(
                self.variables[f'V{height}M']**2
                + self.variables[f'U{height}M']**2
            )
            self.variables[f'wind_speed_{height}_m_per_s'] = self._fill_masked_val(
                self.variables[f'wind_speed_{height}_m_per_s'],
                0.0
            )

        # wind direction
        self.variables[f'wind_direction_deg'] = self._get_wind_direction(
            self.variables['U50M'], 
            self.variables['V50M']
        )

        # wind class
        self.variables[f'wind_turbine_iec_class'] = self._get_wind_turbine_class(
            self.variables['wind_speed_10_m_per_s'],
            self.variables['wind_speed_50_m_per_s']
        )

        # global horizontal irradiance
        self.variables['ghi_w_per_m_2'] = self.variables['SWGDN']
        self.variables['ghi_w_per_m_2'] = self._fill_masked_val(
            self.variables['ghi_w_per_m_2'],
            0.0
        )

    def _load_power_curves(self):
        """Load wind turbine power curves from file.
        
        PySAM requires a relationship between wind speed
        and output power for wind power modeling"""
        wind_power_curve_fields = {
            'Wind Speed'                : 'wind_speed',
            'Composite IEC Class I'     : 1,
            'Composite IEC Class II'    : 2,
            'Composite IEC Class III'   : 3
        }

        self.wind_power_curves = defaultdict(list)
        
        # populate power curves.
        # the file should have three columns with the above fields.
        # each row should have a wind speed and corresponding
        # power output
        with open(self.wind_power_curve_file) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                for key in row:
                    self.wind_power_curves[
                        wind_power_curve_fields[key]
                    ].append(float(row[key]))

    def _load_masks(self):
        if self.mask_files:
            for mask_file in self.mask_files:
                self._add_mask(mask_file)

    def _add_mask(self, mask_file: Path):
        pass

    def _initialize_solar_model(self):
        """Initialize default parameters.
        
        Before running, array tilt and resource data
        need to be assigned
        """
        self.solar_model = pv.default('PVwattsNone')

        self.solar_model.SystemDesign.array_type = 0
        self.solar_model.SystemDesign.system_capacity = 1000
        self.solar_model.SystemDesign.azimuth = 180
        self.solar_model.SystemDesign.dc_ac_ratio = 1.1
        self.solar_model.SystemDesign.inv_eff = 96
        self.solar_model.SystemDesign.losses = 14
        self.solar_model.AdjustmentFactors.constant = 1.0

    def _initialize_wind_model(self):
        """Initialize default parameters.

        Before running, turbine power curve and resource data
        need to be assigned
        """
        self.wind_model = wp.default('WindPowerNone')
        self.wind_model.Resource.wind_resource_model_choice = 0
        self.wind_model.Turbine.wind_turbine_rotor_diameter = 90
        self.wind_model.Turbine.wind_turbine_hub_ht = 80
        self.wind_model.Farm.system_capacity = 1500
        self.wind_model.Farm.wind_farm_wake_model = 0
        self.wind_model.Farm.wind_farm_xCoordinates = np.array([0])
        self.wind_model.Farm.wind_farm_yCoordinates = np.array([0])

    def _initialize_dataset(self, dataset):
        """Create empty netcdf dataset"""
        dataset.createDimension('lat', len(self.variables['lat']))
        dataset.createDimension('lon', len(self.variables['lon']))
        dataset.createDimension('time', HOURS_PER_YEAR)
        dataset.year = self.year

        # create primary variables
        lat_var = dataset.createVariable('lat', 'double', ('lat'))
        lon_var = dataset.createVariable('lon', 'double', ('lon'))
        lat_var[:] = self.variables['lat']
        lon_var[:] = self.variables['lon']

        # create capacity factor variables:
        dataset.createVariable(
            'solar_capacity_factor',
            'double', 
            ('lat', 'lon', 'time')
        )
        dataset.createVariable(
            'wind_capacity_factor',
            'double',
            ('lat', 'lon', 'time')
        )
  
    @staticmethod
    def _get_dni_dhi(lat, lon, year, ghi):
        """Approximate direct normal irradiance (DNI) and 
        diffuse horizontal irradiance (DHI).

        This is necessary because PySAM needs DNI and DHI, 
        but MERRA only provides GHI.
        """
        date_times = pd.date_range(
            datetime(year, 1, 1, 0),
            datetime(year, 12, 31, 23),
            freq=timedelta(hours=1)
        )
        date_times = date_times[(date_times.month != 2) | (date_times.day != 29)]
        solar_position = pvlib.solarposition.get_solarposition(
            date_times,
            lat,
            lon
        )

        # calculate dni 
        # https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.dirint.html
        dni = pvlib.irradiance.dirint(
            ghi,
            solar_position['zenith'],
            date_times
        ).fillna(0).values

        # estimate dhi 
        # https://pvpmc.sandia.gov/modeling-steps/1-weather-design-inputs/irradiance-and-insolation-2/global-horizontal-irradiance/
        dhi = ghi - dni * np.cos(
            solar_position['zenith'] * math.pi / 180
        )

        return date_times, dni, dhi

    def _get_solar_resource_data(self, lat_idx, lat, lon_idx, lon):
        """Populate solar resource data.
        
        https://nrel-pysam.readthedocs.io/en/master/modules/Pvwattsv7.html
        """
        date_times, dni, dhi = self._get_dni_dhi(
            lat, 
            lon, 
            self.year,
            self.variables['ghi_w_per_m_2'][lat_idx, lon_idx, :]
        )

        solar_resource_data = {
            'lat' :     lat,
            'lon' :     lon,
            'tz' :      0,
            'elev' :    0,
            'year' :    list(date_times.year),
            'month' :   list(date_times.month),
            'day' :     list(date_times.day),
            'hour' :    list(date_times.hour),
            'minute' :  list(date_times.minute),
            'dn' :      list(dni),
            'df' :      list(dhi),
            'tdry' :    list(self.variables['temperature_c'][lat_idx, lon_idx, :]),
            'wspd' :    list(self.variables['wind_speed_2_m_per_s'][lat_idx, lon_idx, :])
        }

        return solar_resource_data

    def simulate_solar(self, solar_resource_data, tilt):
        """Simulate solar output. Return hourly capacity factors"""
        # assign parameters and resource data
        self.solar_model.SystemDesign.tilt = tilt
        self.solar_model.SolarResource.solar_resource_data = solar_resource_data
        self.solar_model.execute()
        solar_generation = np.array(self.solar_model.Outputs.ac)

        return solar_generation / (self.solar_model.SystemDesign.system_capacity * 1000)

    def _get_wind_resource_data(self, lat_idx, lon_idx):
        """Populate wind resource data.
        
        Primary documentation for PySAM WindPower does not 
        describe what the wind_resource_data dict should look like.
        Instead, the format is assumed from PySAM's source code.
        https://github.com/NREL/pysam/blob/d269cab0dbcaeaa2e5126decb9d1114e6dd83dc4/files/ResourceTools.py
        """
        wind_resource_data = {
            'heights' : [],
            'fields' : [],
            'data' : []            
        }

        # these are the possible fields
        field_names = ('temperature', 'pressure', 'speed', 'direction')

        # these are the fields we have data for
        fields = [
            (2, 'temperature'),
            (2, 'pressure'),
            (2, 'speed'),
            (10, 'speed'),
            (50, 'speed'),
            (50, 'direction')
        ]

        # this dictionary maps the fields we have data for
        # to their variable names
        field_variables = {
            (2, 'temperature') : 'temperature_c',
            (2, 'pressure') : 'pressure_atm',
            (2, 'speed') : 'wind_speed_2_m_per_s',
            (10, 'speed') : 'wind_speed_10_m_per_s',
            (50, 'speed') : 'wind_speed_50_m_per_s',
            (50, 'direction') : 'wind_direction_deg',
        }

        # append header information
        for height, field_name in fields:
            wind_resource_data['heights'].append(height)
            wind_resource_data['fields'].append(field_names.index(field_name) + 1)

        # append hourly data rows
        for hour in range(HOURS_PER_YEAR):
            data_row = [
                self.variables[field_variables[field]][lat_idx, lon_idx, hour]
                for field in fields
            ]
            wind_resource_data['data'].append(data_row)

        return wind_resource_data

    def simulate_wind(self, wind_resource_data, wind_turbine_class):
        """Simulate wind output. Return hourly wind capacity factors"""
        # assign parameters and resource data
        self.wind_model.Turbine.wind_turbine_powercurve_windspeeds = self.wind_power_curves[
            'wind_speed'
        ]
        self.wind_model.Turbine.wind_turbine_powercurve_powerout = self.wind_power_curves[
            wind_turbine_class
        ]
        self.wind_model.Resource.wind_resource_data = wind_resource_data
        self.wind_model.execute()
        wind_generation = np.array(self.wind_model.Outputs.gen) 

        return wind_generation / self.wind_model.Farm.system_capacity 
        
    def run(self):
        """Calculate hourly solar and wind capacity factors,
        and store output in a netCDF file
        """
        # initialize output directory
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # setup solar and wind models
        self._initialize_solar_model()
        self._initialize_wind_model()

        # run and store output
        with Dataset(self.output_file, 'w') as dataset:
            # setup empty dataset
            self.variables['lat'] = self.variables['lat'][:3]
            self.variables['lon'] = self.variables['lon'][:3]
            self._initialize_dataset(dataset)

            # run power simulation
            for lat_idx, lat in enumerate(self.variables['lat']):
                for lon_idx, lon in enumerate(self.variables['lon']):
                    logging.info(f'Calculating power generation for {lat:.2f}, {lon:.2f} (lat, lon)...')
                    # get solar resource data                    
                    solar_resource_data = self._get_solar_resource_data(
                        lat_idx,
                        lat,
                        lon_idx,
                        lon
                    )

                    # run PySAM solar
                    solar_capacity_factors = self.simulate_solar(
                        solar_resource_data,
                        abs(lat)
                    )

                    # write solar generation
                    dataset.variables['solar_capacity_factor'][lat_idx, lon_idx] = solar_capacity_factors

                    # get wind resource data
                    wind_resource_data = self._get_wind_resource_data(
                        lat_idx,
                        lon_idx
                    )

                    # run PySAM wind
                    wind_capacity_factors = self.simulate_wind(
                        wind_resource_data, 
                        self.variables['wind_turbine_iec_class'][lat_idx, lon_idx]
                        )

                    # write wind generation
                    dataset.variables['wind_capacity_factor'][lat_idx, lon_idx] = wind_capacity_factors

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('combined_merra_file', type=Path)
    parser.add_argument('output_file', type=Path)
    parser.add_argument(
        '--wind-power-curve-file',
        type=Path,
        default=Path(
            PROJECT_PATH, 
            'input',
            'power_curves', 
            'wind_turbine_power_curves.csv'
        )
    )

    args = parser.parse_args()

    power_generation = MerraPowerGeneration(
        args.combined_merra_file,
        args.output_file,
        args.wind_power_curve_file
    )

    power_generation.run()
