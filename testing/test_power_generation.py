import unittest
from sys import path
from pathlib import Path 

path.insert(0, Path(Path(__file__), '..', 'src')

class TestPowerGeneration(unittest.TestCase):

	def test_import(self):
		from powGen_impl_beta import main
		pass

if __name__ == "__main__":
	unittest.main()