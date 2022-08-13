import unittest
import sys
import os

sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','src'))

class TestPowerGeneration(unittest.TestCase):

	def test_import(self):
		from power_generation import main
		pass

if __name__ == "__main__":
	unittest.main()