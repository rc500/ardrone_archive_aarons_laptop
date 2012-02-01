#!/usr/bin/python
import sys
import os

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_uav import DroneApp as app

if __name__ == '__main__':
	MAIN_APP = app.DroneApp()
	MAIN_APP.run()
