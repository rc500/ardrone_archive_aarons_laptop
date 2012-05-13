import os
import signal
import sys

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import objects to initialise
from ardrone.core.controlloop import ControlLoop
from ardrone.platform import qt as platform
from . import DroneControl
from . import SwarmControl
from . import StatusUpdater

class AppController(object):
	"""
	Initially sets up system in configuration provided. Routes communication of status messages to status updater.
	"""
	def __init__(self,drones,configs):
		# ---- DRONES SETUP ----
		# List of ControlLoop objects for use in interfacing with drones
		control_loops = []

		for index in range (0,len(drones)):
			# Attempt to open a connection to the drone
			connection = platform.Connection() # do we want to keep a copy of this?
			# Create ControlLoop object to interface with drone
			control_loops.append(ControlLoop(connection, **configs[index]))
		
		# ---- INITIALISE APPLICATION OBJECTS ----
		# List of DroneControl objects for use in managing individual drone actions
		self.drone_controls = []
		
		# DroneControl
		for index in range(0,len(drones)):
			self.drone_controls.append(DroneControl.DroneControl(drones[index],control_loops[index],configs[index],self))

		# SwarmControl
		self._swarm_control = SwarmControl.SwarmControl(drones,tuple(self.drone_controls))

		# StatusUpdater
		self._status_updater = StatusUpdater.StatusUpdater(drones,tuple(self.drone_controls),self._swarm_control)

	def start(self):
		"""
		Start app
		"""
		print ("start called - AppController")
		self._swarm_control.start_program()

	def update(self,something):
		"""
		Passes on updates to status updater
		"""
		self._status_updater.update(something)
