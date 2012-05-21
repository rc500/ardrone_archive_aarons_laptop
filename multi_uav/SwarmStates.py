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
	As status messages are received, the state machine determines the next state and changes it accordingly.
	
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
		If state requires changing then do so to the correct state.
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
		if state_id == 0:
			self._coop.change_state((SetupState(self._coop,self.drones,self.drone_controllers),0))
		elif state_id == 1:
			self._coop.change_state((TaskBad(self._coop,self.drones,self.drone_controllers),1))
		elif state_id == 2:
			self._coop.change_state((TaskGood(self._coop,self.drones,self.drone_controllers),2))

class SetupState(State):
	"""
	ID = 0
	
	The SetupState is for when the drones are not verified as being ready for operations.
	State entry requirements: none
	State purpose: to WAIT until drones are hovering stably
	
	State transition conditions:

	State 0:
	-

	State 1:
	height_stable == True for all drones

	State 2:
	-
	"""
		
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {'height_stable':True}, {}]
		self.exit_conditional = ['none','and','none']
		print("======In Setup State======")

	def maintain(self):
		for drone in self.drone_controllers:
			drone.request_state(2)

	def transition(self,state_id):
		self.maintain()
		self.check_exit()
			
class TaskBad(State):
	"""
	ID = 1
	
	The GroundState state for when task is not being achieved.
	State entry requirements: assets are ready.
	State purpose: to achieved the task.

	TASK - to move continuously around a loop without collision
	
	State transition conditions:

	State 0:
	-

	State 1:
	-

	State 2:
	airprox == False && following_marker == True

	"""
	
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {},{'airprox':False, 'following_marker':True}]
		self.exit_conditional = ['none','none','and']

		# Ask each drone to hold current position
		self._coop.send_routes(self._coop._navigator.hold_position_route(self._coop.swarm_status['position']),self.drones)

		print("======Task not being achieved======")
	
	def maintain(self):
		self.check_exit()
		pass # It's not hard to carry on doing something badly!

	def transition(self,state_id):
		if state_id == 0 or state_id == 1:
			print("Trying to change from TaskBad state into a SwarmState which isn't sensible. No action taken - SwarmState")
		
		if state_id == 2:
			# Continue route for front-most drone only to increase separation
			new_routes = self._coop._navigator.route(self._coop.swarm_status['position'])
			self._coop.send_routes(new_routes,[self._coop._navigator.front_drone(),])
			# Request drones to move into a state able to follow markers
			for drone in self.drone_controllers:
				drone.request_state(3)
			# Check success
			self.check_exit()
				
class TaskGood(State):
	"""
	ID = 2
	
	The CooperativeController state for when the task is being achieved.
	State entry requirements: task is being achieved.
	State purpose: watch over situation to detect danger to both task and assets.
	
	TASK - to move continuously around a loop without collision
	
	State transition conditions:

	State 0:
	-

	State 1:
	airprox == True || following_marker == False

	State 2:
	-
	"""
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {'airprox':True,'following_marker':False}, {}]
		self.exit_conditional = ['none','or','none']
		print("======Task being achieved======")

	def maintain(self):
		# Continue route
		new_routes = self._coop._navigator.route(self._coop.swarm_status['position'],self.drones)
		print("new routes: %s" %new_routes)
		self._coop.send_routes(new_routes)

		# Check State
		self.check_exit()

		# will want to control spacings here

	def transition(self,state_id):
		pass
		# nothing yet - or ever?
