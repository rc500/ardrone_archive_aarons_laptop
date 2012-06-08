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
	def __init__(self,drones,drone_controllers,homes): # Will want to add in _drone2 in time
		# --- STORE VARIABLES ---
		self.drones = drones # tuple of drone ids
		self.swarm_status = {};		
		self.homes = homes

		# --- STORE POINTERS ---
		self.drone_controllers = drone_controllers

		# --- INITIALISE APPLICATION OBJECTS ----
		#self._status_viewer = # add at some point
		self._navigator = Navigator.Navigator(self.drones,self.homes)	

		# Setup timer to detect for state changes
		self.check_timer = QtCore.QTimer()
		self.check_timer.setInterval(1000) # ms
		self.check_timer.timeout.connect(self.action)

		# Setup timer to start simulated battery low after event
		self.simulate_timer = QtCore.QTimer()
		self.simulate_timer.setInterval(5000) # ms
		self.simulate_timer.timeout.connect(self.simulate)

		# States
		self._state = -1
		self.state_id = -1

		# Simulation
		self.simulate_flag = False
		self.timer_flag = False

		# Variables
		self.min_separation = -1
		self.asset_drone = -1 # drone_id of drone allocated to perform task
		self.asset_drone_controller = -2 # drone controller of drone allocated to perform task
		self.low_battery_drones = []

	def start_program(self):
		print("======Program started======")
		# Enter initial state
		self._state = State.SetupState(self,self.drones,self.drone_controllers)
		self._state.next_state(0)

		# Start SwarmControl timing loop	
		self.check_timer.start()

	def simulate(self):
		"""
		Set simulation flag which is read by StatusUpdater for simulation purposes
		"""
		print("simulate_flag set true")
		self.simulate_flag = True
		self.simulate_timer.stop()

	def action(self):
		"""
		Called by local timer to decide what to do at regular intervals.
		The general idea is to always aim for a better state.
		The actions here are then propogated into SwarmStates and down to individual drone controllers.

		State id 0 = SetupState
		State id 1 = TaskBad (i.e. Task not being achieved for some reason)
		State id 2 = TaskGood (i.e. Task being achieved)

		Only one state transition should occur every time action is called.
		"""
		# Update separation
		self.min_separation = self._navigator.min_separation(self.swarm_status['position'])
		# Check whether simulation required
		#print("drone batteries are: %s" % self.swarm_status['battery'])
		if not self.swarm_status['observer'] == -1 and self.timer_flag == False:
			self.timer_flag = True
			self.simulate_timer.start()
		# First, go into Setup State
		if self.state_id == -1:
			self.transition_to_state(0)
		# If in Setup State, then transition to Bad State
		elif self.state_id == 0:
			self.transition_to_state(1)
		# If in Bad State, then transition to Good State
		elif self.state_id == 1:
			self.transition_to_state(2)
		# If in Good State, then maintain
		elif self.state_id == 2:
			self.maintain_state()

	def send_routes(self,routes,send_to):
		"""
		Function which pipes routes to drones in the form of a list of marker ids.
		Only drone ids defined in the 'send_to' parameter are sent to.

		send_to must be a list or tuple.
		"""
		for drone in self.drones:
			if drone in send_to:
				#print("update drone %s with route %s" % (drone,routes[self.drones.index(drone)]))
				self.drone_controllers[self.drones.index(drone)].update_route(routes[self.drones.index(drone)])

	def maintain_state(self):
		"""
		Request the current state to maintain itself
		"""
		self._state.maintain()

	def transition_to_state(self,state_id):
		"""
		Request the current state to progress to a new state
		"""
		self._state.transition(state_id)

	def land_low_battery_drones(self):
		"""
		Send all drones with low battery back home to land.
		Must ensure that there is always one drone still heading to complete/is completing the task before exiting.
		"""				
		for index in range(0,len(self.drones)):
			# If drone's battery is too low, send it home and add it to the list of low battery drones
			if self.swarm_status['battery'][index]<15:
				# Add to list if not already present
				if self.drones[index] not in self.low_battery_drones:
					self.low_battery_drones.append(self.drones[index])

				# New routes home
				self.drone_controllers[index].request_state(3)
				new_routes = self._navigator.route_to_target(self.swarm_status['position'][index],self.homes[index],self.drones[index])
				self.send_routes(new_routes,[self.drones[index],])
				
				# If drone's battery is too low and it is at home position, land it 	
				if self.swarm_status['position'][index]==self.homes[index]:
					self.drone_controllers[index].land()

				# If this drone was the asset, then unallocate it
				if self.drones[index] == self.asset_drone:
					self.remove_current_asset()

	def allocate_asset(self):
		"""
		If there is no current asset, designate the most suitable drone to carry out task.
		Most suitable = highest battery.
		Do not allocate drones which are low on battery.
		Return True if asset is available, False if not.
		"""				
		if self.asset_drone == -1:
			# set _drone to be drone_id of drone with highest battery
			# and _drone_controller to be the corresponding controller
			self.asset_drone = self.drones[self.swarm_status['battery'].index(max(self.swarm_status['battery']))]
			if self.asset_drone in self.low_battery_drones:
				self.asset_drone = -1
				return False
			else:
				self.asset_drone_controller = self.drone_controllers[self.drones.index(self.asset_drone)]
				return True
		else:
			return True
		#print("allocating new asset: %s" % self.asset_drone)
	
	def remove_current_asset(self):
		"""
		Remove current asset
		"""		
		self.asset_drone = -1
		self.asset_drone_controller = -1
		#print("removing current asset")

	def update(self,status):
		self.swarm_status = status
				
	def change_state(self,state):
		"""
		Function called so SwarmControl object knows which is the current state
		"""
		self._state = state[0]
		self.state_id = state[1]

