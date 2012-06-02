import os
import sys
import json, socket, time

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')

class State(object):
	"""
	A class which manages the state of the SwarmController object.
	This is the base class from which all states inherit.
	
	A state can be requested to be maintained:
	>> maintain()

	or a requested to try to transition to a new state:
	>> transition(state_id)

	When it is requested to do so, the state machine determines whether it is in the correct state and changes it accordingly.
	State changes are checked by comparing the current swarm_status against the exit_conditions of the current state.

	The state ids are:
	0	- Setup State (i.e. setting up to a pre-mission configuration)
	1	- TaskBad (i.e. task not being achieved)
	2	- TaskGood (i.e. task being achieved)
	"""
	def __init__(self,_coop,drones,drone_controllers):
		
		# Variables
		self.drones = drones
		self.state_ids = (0,1,2)

		# Assign pointers
		self.drone_controllers = drone_controllers # NB - actually a tuple of pointers
		self._coop = _coop

	def transition(self,state_id):
		"""
		Carry out action to transition towards requested state.
		"""
		pass

	def maintain(self):
		"""
		Carry out action to maintain state.
		"""
		pass

	def check_exit(self):
		"""
		Check the exit conditions against swarm status.
		If state requires changing then do so to the correct state and inform SwarmControl of this change.
		"""
		# Count for conditions which have been met
		conditions_met_count = 0

		# Check exit condition for each state against all exit conditions for the respective state
		for state in self.state_ids:
			for key in self.exit_conditions[state].keys():
				#print ("checking condition against: %s" % key)
				#print ("comparisson: %s" % ([self.exit_conditions[state][key],self._coop.swarm_status[key]]))
				if self.exit_conditions[state][key] == self._coop.swarm_status[key]:
					conditions_met_count = conditions_met_count + 1

			# Check met conditions against total conditions, accept or reject exit as specified in state
			if self.exit_conditional[state] == 'none':
				pass
			elif conditions_met_count == len(self.exit_conditions[state]):
				self.next_state(state)
			elif conditions_met_count > 0 and self.exit_conditional[state] == 'or':
				self.next_state(state)
			elif conditions_met_count == 0 or self.exit_conditional[state] == 'and':
				pass
			else: 
				print("Unexpected condition grouping - check_exit - SwarmStates")

	def next_state(self,state_id):
		"""
		Takes a state_id and changes the current state to the relevant object.
		"""
		if state_id == 0:
			self._coop.change_state((SetupState(self._coop,self.drones,self.drone_controllers),0))
		elif state_id == 1:
			self._coop.change_state((TaskBad(self._coop,self.drones,self.drone_controllers),1))
		elif state_id == 2:
			self._coop.change_state((TaskGood(self._coop,self.drones,self.drone_controllers),2))

class SetupState(State):
	"""
	state_id = 0
	
	The SetupState is for when the drones are not verified as being ready for operations.
	State entry requirements: none
	State purpose: to WAIT until drones are communicating
	
	State transition conditions:

	State 0:
	-

	State 1:
	talking == True for all drones

	State 2:
	-
	"""
		
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {'talking':True}, {}]
		self.exit_conditional = ['none','and','none']
		print("======In Setup State======")

	def maintain(self):
		for drone in self.drone_controllers:
			drone.request_state(0)

	def transition(self,state_id):
		self.maintain()
		self.check_exit()
		for drone in self.drone_controllers:
			drone.request_state(0)
			
class TaskBad(State):
	"""
	state_id = 1
	
	The TaskBad state is for when the task is not being achieved.
	State entry requirements: drones are setup and ready for operations.
	State purpose: to achieved the task.

	TASK - to observe marker 0.
	
	State transition conditions:

	State 0:
	-

	State 1:
	-

	State 2:
	airprox == False && observing_target == True 

	"""
	
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {},{'airprox':False, 'observing_target':True}]
		self.exit_conditional = ['none','none','and']

		# Ask each drone to hold current position
		#self._coop.send_routes(self._coop._navigator.hold_position_route(self._coop.swarm_status['position']),self.drones)
		print("======Task not being achieved======")
	
	def maintain(self):
		self.check_exit()
		pass # It's not hard to carry on doing something badly!

	def transition(self,state_id):
		if state_id == 0 or state_id == 1:
			print("Trying to change from TaskBad state into a SwarmState which isn't sensible. No action taken - SwarmState")
		
		if state_id == 2:
			"""
			To achieve the task, find the drone with highest battery percentage and navigate it to the target
			"""
			# set _drone to be drone_id of drone with highest battery
			# and _drone_controller to be the corresponding controller
			_drone = self.drones[self._coop.swarm_status['battery'].index(max(self._coop.swarm_status['battery']))]
			_drone_controller = self.drone_controllers[self.drones.index(_drone)]

			# request this drone to enter a state ready to follow markers
			_drone_controller.request_state(3)

			# if position of drone is known, then request the drone follow a route to the target
			# (NB this will only do something when the drone is in state 3)
			new_routes = self._coop._navigator.route_to_target(self._coop.swarm_status['position'][self.drones.index(_drone)],0,_drone)
			self._coop.send_routes(new_routes,[_drone,])

			# Check success
			self.check_exit()
				
class TaskGood(State):
	"""
	ID = 2
	
	The TaskGood state is for when the task is being achieved.
	State entry requirements: task is being achieved.
	State purpose: watch over situation to check for task not being achieved.
	
	TASK - to move continuously around a loop without collision
	
	State transition conditions:

	State 0:
	-

	State 1:
	airprox == True || observing_target == False

	State 2:
	-
	"""
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {'airprox':True,'observing_target':False}, {}]
		self.exit_conditional = ['none','or','none']
		print("======Task being achieved======")

	def maintain(self):
		# Don't have to do anything to maintain current state as observation is static

		# Check State
		self.check_exit()

	def transition(self,state_id):
		# Check State
		self.check_exit()
