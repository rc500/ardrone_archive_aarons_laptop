import os
import sys
import socket, time

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')

# Import helpful classes
from . import SwarmStates as State
from . import Navigator

class SwarmControl(object):
	"""
	The base class for overseeing cooperative control of multiple drones.

	Uses navigation logic (from Navigator class) and task logic (from Task States) to decide on actions.
	Actions are sent to each drone's Individual Controller.
	"""

	def __init__(self,drones,drone_controllers): # Will want to add in _drone2 in time
		# --- STORE VARIABLES ---
		self.drones = drones # tuple of drone ids
		self.swarm_status = {};		

		# --- STORE POINTERS ---
		self.drone_controllers = drone_controllers

		# --- INITIALISE APPLICATION OBJECTS ----
		#self._status_viewer = # add at some point
		self._navigator = Navigator.Navigator(self.drones)	

		# Setup timer to detect for state changes
		self.check_timer = QtCore.QTimer()
		self.check_timer.setInterval(5000) # ms
		self.check_timer.timeout.connect(self.action)

		# States
		self._state = -1
		self.state_id = -1
	
		# Start program
		self.start_program()
		
	def start_program(self):
		print("======Program started======")
		# Enter initial state
		self._state = State.SetupState(self,self.drones,self.drone_controllers)

		# Start SwarmControl timing loop	
		self.check_timer.start()

	def action(self):
		"""
		Decide what to do.
		"""
		# First, go into Setup State
		if self.state_id == -1:
			self.transition_to_state(0)

	def send_routes(self,routes):
		"""
		Function which gives each drone a route in the form of a list of marker ids.
		"""
		local_drone = list(self.drone_controllers)
		local_drone.reverse()

		for route in routes:
			print "update drone with route"
			local_drone.pop().update_route(route)

	def maintain_state(self):
		"""
		Maintain current state.
		"""
		self._state.maintain()

	def transition_to_state(self,state_id):
		"""
		Progress to new state.
		"""
		self._state.transition(state_id)

	def update(self,status):
		self.swarm_status = status
				
	def change_state(self,state):
		"""
		Function called to update the state used by the SwarmController object
		"""
		self._state = state[0]
		self.state_id = state[1]

