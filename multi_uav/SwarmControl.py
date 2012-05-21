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

	Uses navigation logic (from Navigator class) and task logic (from Swarm States) to decide on actions.
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
		self.check_timer.setInterval(1000) # ms
		self.check_timer.timeout.connect(self.action)

		# States
		self._state = -1
		self.state_id = -1
		
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

		# If in Setup State, then transition to Bad State
		if self.state_id == 0:
			self.transition_to_state(1)

		# If in Bad State, then transition to Good State
		if self.state_id == 1:
			self.transition_to_state(2)

		# If in Good State, then maintain
		if self.state_id == 2:
			self.maintain_state()

	def send_routes(self,routes,send_to):
		"""
		Function which gives drones a route in the form of a list of marker ids.
		Only drone ids defined in the 'send_to' parameter are sent to.

		send_to must be a list or tuple
		"""
		for drone in self.drones:
			if drone in send_to:
				print("update drone %s with route" % (drone))
				self.drone_controllers[self.drones.index(drone)].update_route(routes[self.drones.index(drone)])

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

