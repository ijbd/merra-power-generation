import unittest
from sys import path
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

# update path
PROJECT_PATH = Path(__file__).parents[1]
path.insert(0, str(Path(PROJECT_PATH, 'src')))

from power_generation import MerraPowerGeneration

class TestPowerGeneration(unittest.TestCase):
	def setUp(self):
		self.combined_merra_file = Path(
			PROJECT_PATH,
			'test_data',
			'combined_merra',
			'combined_merra_2020.nc'
		)
		self.output_file = Path(
			PROJECT_PATH, 
			'test_data', 
			'tmp_merra_power_generation_2020.nc'
		)
		self.wind_power_curve_file = Path(
            PROJECT_PATH, 
            'input',
            'power_curves', 
            'wind_turbine_power_curves.csv'
        )

	def test_power_generation(self):
		mpg = MerraPowerGeneration(
			self.combined_merra_file,
			self.output_file,
			self.wind_power_curve_file
    	)

		mpg.run()

	def test_power_generation_common_sense_solar(self):
		with Dataset(self.output_file) as output:
			with Dataset(self.combined_merra_file) as combined:
				solar_predictor = combined.variables['SWGDN'][:]
				wind_predictor = np.sqrt(
					combined.variables['U50M'][:]**2 \
					+ combined.variables['V50M'][:]**2
				)

				solar_cf = output.variables['solar_capacity_factor'][:]
				wind_cf = output.variables['wind_capacity_factor'][:]

		solar_correlation = np.corrcoef(
			solar_predictor.flatten(),
			solar_cf.flatten()
			)[0,1]
		wind_correlation = np.corrcoef(
			wind_predictor.flatten(),
			wind_cf.flatten()
			)[0,1]

		correlation_threshold = 0.8

		self.assertGreater(solar_correlation, correlation_threshold)
		self.assertGreater(wind_correlation, correlation_threshold)

if __name__ == "__main__":
	unittest.main()