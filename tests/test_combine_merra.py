import unittest
from sys import path
from pathlib import Path
from netCDF4 import Dataset
from numpy import array_equal

# update path
PROJECT_PATH = Path(__file__).parents[1]
path.insert(0, str(Path(PROJECT_PATH, 'src')))

from combine_merra import combine, MERRA_VARIABLES

class TestCombineMerra(unittest.TestCase):
	def setUp(self):
		self.test_merra_path = Path(PROJECT_PATH, 'test_data', 'merra')
		self.test_year = 2020
		self.test_output_file = Path(
			PROJECT_PATH, 
			'test_data', 
			'tmp_combined_merra_2020.nc'
		)

		combine(self.test_merra_path, self.test_year, self.test_output_file)
		
		with Dataset(self.test_output_file) as dataset:
			self.output_lats = dataset.variables['lat'][:]
			self.output_lons = dataset.variables['lon'][:]
			self.output_vars = { 
				variable : dataset.variables[variable][:] 
				for variable in MERRA_VARIABLES
			}

	def tearDown(self):
		self.test_output_file.unlink()

	def test_combined_day_one(self):
		# open original day 1
		with Dataset(Path(
			PROJECT_PATH, 
			'test_data', 
			'merra', 
			'MERRA2_400.tavg1_2d_rad_Nx.20200101.nc4.nc4'
		)) as dataset:
			original_lats = dataset.variables['lat'][:]
			original_lons = dataset.variables['lon'][:]
			original_swgdn = dataset.variables['SWGDN'][:]

		# check lat lons
		self.assertTrue(array_equal(original_lats, self.output_lats))
		self.assertTrue(array_equal(original_lons, self.output_lons))

		# check corners
		end_hour = 23
		self.assertEqual(
			original_swgdn[0,0,0], 
			self.output_vars['SWGDN'][0,0,0]
		)
		self.assertEqual(
			original_swgdn[-1,0,0], 
			self.output_vars['SWGDN'][0,0,end_hour]
		)
		self.assertEqual(
			original_swgdn[0,-1,0],
			self.output_vars['SWGDN'][-1,0,0]
		)
		self.assertEqual(
			original_swgdn[0,0,-1],
			self.output_vars['SWGDN'][0,-1,0]
		)

	def test_combined_day_five(self):
		# open original day 3
		with Dataset(Path(
			PROJECT_PATH, 
			'test_data', 
			'merra', 
			'MERRA2_400.tavg1_2d_slv_Nx.20200103.nc4.nc4'
		)) as dataset:
			original_lats = dataset.variables['lat'][:]
			original_lons = dataset.variables['lon'][:]
			original_t2m = dataset.variables['T2M'][:]

		# check lat lons
		self.assertTrue(array_equal(original_lats, self.output_lats))
		self.assertTrue(array_equal(original_lons, self.output_lons))

		# third day hour
		start_hour = 2*24
		end_hour = (3*24) - 1

		# check corners
		self.assertEqual(
			original_t2m[0,0,0],
			self.output_vars['T2M'][0,0,start_hour]
		)
		self.assertEqual(
			original_t2m[-1,0,0],
			self.output_vars['T2M'][0,0,end_hour]
		)
		self.assertEqual(
			original_t2m[0,-1,0],
			self.output_vars['T2M'][-1,0,start_hour]
		)
		self.assertEqual(
			original_t2m[0,0,-1],
			self.output_vars['T2M'][0,-1,start_hour]
		)

if __name__ == "__main__":
	unittest.main()