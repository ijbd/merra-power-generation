import unittest
from sys import path
from pathlib import Path
from netCDF4 import Dataset
from numpy import array_equal

# update path
PROJECT_PATH = Path(__file__).parents[1]
path.insert(0, str(Path(PROJECT_PATH, 'src')))

from power_generation import MerraPowerGeneration

class TestPowerGeneration(unittest.TestCase):
	def setUp(self):
		self.combined_merra_path = Path(
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

	def tearDown(self):
		self.test_output_file.unlink()

	def test_power_generation(self):
		mpg = MerraPowerGeneration(
			self.combined_merra_file,
			self.output_file,
			self.wind_power_curve_file
    	)

		mpg.run()

	def test_one_mask(self):
		pass

	def test_multi_mask(self):
		pass

if __name__ == "__main__":
	unittest.main()