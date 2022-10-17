from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
from typing import List
import logging
import math
import csv
from datetime import datetime

from netCDF4 import Dataset
import numpy as np
import pandas as pd
import pvlib
import PySAM.Pvwattsv7 as pv
import PySAM.Windpower as wp

# setup logging
logging.basicConfig(level=logging.DEBUG)

PROJECT_PATH = Path(__file__).parents[1]
ATM_PER_PASCAL = 1 / 101325
KELV_CELSIUS_OFFSET = 273.15

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
        logging.info(f'Loading MERRA data from {self.combined_merra_file}...')
        with Dataset(self.combined_merra_file) as dataset:
            self.year = dataset.year
            self.variables = {name : np.array(var[:]) for name, var in dataset.variables.items()}

    @staticmethod
    def _get_wind_direction(eastward_velocity, northward_velocity):
        """ Get wind travel direction as an angle from due south:

            0 -> due south
            90 -> due west
            180 -> due north
            270 -> due east
        """
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
        height_3):
        """TODO double check this formulation, it seems odd that height_3 is not an input
        """
        wind_scale = math.log(height_2, height_1)
        wind_sheer = np.log(wind_speed_height_2 / wind_speed_height_1) / wind_scale
        wind_speed_height_3 = wind_speed_height_2 * (2 ** wind_sheer)
        return wind_speed_height_3

    @staticmethod
    def _get_wind_turbine_class(wind_speed_10, wind_speed_50):
        """TODO: 
            - Implement offshore mask. 
            - Add offshore.
            - Add multi-year
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

        print(median_wind_speed.astype(int))
        # distribute wind locations among 3 IEC turbine classes
        wind_turbine_class = np.where(median_wind_speed >= 8, 2, 3)
        wind_turbine_class = np.where(median_wind_speed >= 9, 1, wind_turbine_class)

        print(wind_turbine_class)
        return wind_turbine_class
        
    def _process_merra_data(self):
        # pressure in atmospheres
        self.variables['pressure_atm'] = self.variables['PS'] * ATM_PER_PASCAL

        # temperature in C
        self.variables['temperature_c'] = self.variables['T2M'] - KELV_CELSIUS_OFFSET

        # wind speed
        for height in [2, 10, 50]:
            # wind speed
            self.variables[f'wind_speed_{height}_m_per_s'] = np.sqrt(
                self.variables[f'V{height}M']**2
                + self.variables[f'U{height}M']**2
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

    def _load_power_curves(self):
        self.wind_power_curves = defaultdict(list)
        with open(self.wind_power_curve_file) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                for key in row:
                    self.wind_power_curves[key].append(row[key])

    def _load_masks(self):
        if self.mask_files:
            for mask_file in self.mask_files:
                self._add_mask(mask_file)

    def _add_mask(self, mask_file: Path):
        pass

    def _initialize_solar_model(self):
        """Still need to define tilt
        """
        return
        self.solar_model = pv.default('PVWattsNone')

        self.solar_model.SystemDesign.array_type = 0
        self.solar_model.SystemDesign.system_capacity = 1000
        self.solar_model.SystemDesign.aziumuth = 180
        self.solar_model.SystemDesign.dc_ac_ratio = 1.1
        self.solar_model.SystemDesign.inv_eff = 96
        self.solar_model.SystemDesign.losses = 14

    def _initialize_wind_model(self):
        """Still need to define powercurve
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
        dataset.createDimension('lat', len(self.variables['lat']))
        dataset.createDimension('lon', len(self.variables['lon']))
        dataset.createDimension('time', 8760)
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
        """TODO double check documentation on all of these"""

        # timestamps
        date_times = pd.date_range(
            datetime(year, 1, 1),
            datetime(year, 12, 31)
        )
        date_times = date_times[(date_times.month != 2) | (date_times.day != 29)]

        # get solar angles
        lat_rad = lat * math.pi / 180
        eq_of_time_min = pvlib.solarposition.declination_spencer71(
            julian_date
        )
        declination_rad = pvlib.solarposition.hour_angle(
            date_times, 
            lon, 
            eq_of_time_min
        )
        hour_angle_deg = pv.solarposition.hour_angle(
            date_times,
            lon,
            eq_of_time_min
        )
        hour_angle_rad = hour_angle_deg * 180 / math.pi
        zenith_rad = pvlib.solarposition.solar_zenith_analytical(
            lat_rad,
            hour_angle_rad,
            declination_rad
        )
        zenith_deg = zenith_rad * 180 / math.pi

        # calculate irradiance
        dni = pvlib.irradiance.dirint(
            ghi,
            zenith_deg,
            date_times
        ).fillna(0)

        dhi = ghi - dni * np.cos(zenith_rad)

        return dni, dhi

    def _get_solar_resource_data(self, lat_idx, lat, lon_idx, lon):
        dni, dhi = self._get_dni_dhi(
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
            'dn' :      dni,
            'df' :      dhi,
            'tdry' :    self.variables['temperature_c'][lat_idx, lon_idx, :],
            'wspd' :    self.variables['wind_speed_2_m_per_s'][lat_idx, lon_idx, :]
        }

        return solar_resource_data

    def simulate_solar(self, solar_resource_data):
        # assign parameters and resource data
        self.solar_model.SystemDesign.tilt = abs(solar_resource_data['lat'])
        self.solar_model.solar_resource_data = solar_resource_data
        self.solar_model.execute()
        solar_generation = np.array(self.solar_model.Outputs.ac)

        return solar_generation / (self.solar_model.SystemDesign.system_capacity * 1000)

    def _get_wind_resource_data(self, lat_idx, lat, lon_idx, lon):
        wind_resource_data = {
            ''
        }

        return wind_resource_data

    def simulate_wind(self, wind_resource_data, wind_class):
        # assign parameters and resource data
        self.wind_model.Resource.wind_resource_data = wind_resource_data
        self.wind_model.Turbine.wind_turbine_powercurve_powerout = self.wind_power_curves['speed']
        self.wind_model.Turbine.wind_turbine_powercurve_windspeeds = self.wind_power_curves[wind_class]
        wind_generation = np.array(self.wind_modeOutputs.gen) 

        return wind_generation / self.wind_model.Farm.system_capacity 
        
    def run(self):
        # initialize output directory
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # setup solar and wind models
        self._initialize_solar_model()
        self._initialize_wind_model()

        # run and store output
        with Dataset(self.output_file, 'w') as dataset:
            # setup empty dataset
            self._initialize_dataset(dataset)

            # run power simulation
            for lat_idx, lat in enumerate(self.variables['lat']):
                for lon_idx, lon in enumerate(self.variables['lon']):
                    # get solar resource data
                    solar_resource_data = self._get_solar_resource_data(
                        lat_idx,
                        lat,
                        lon_idx,
                        lon
                    )

                    # run PySAM solar
                    solar_capacity_factors = self.simulate_solar(solar_resource_data)

                    # write solar generation
                    pass

                    # get wind resource data
                    wind_resource_data = self._get_wind_resource_data(
                        lat_idx,
                        lat,
                        lon_idx,
                        lon
                    )

                    # run PySAM wind
                    wind_capacity_factors = self.simulate_wind(wind_resource_data)

                    # write wind generation
                    pass

if __name__ == "__main__":
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
