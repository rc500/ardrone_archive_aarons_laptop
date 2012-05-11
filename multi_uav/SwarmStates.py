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
	"""
	swarm_status =
					{
					'talking': False
					'following_marker': False
					'position':[]
					# etc.
					}
	"""
	def __init__(self,_coop,drones,drone_controllers):
		
		# Variables
		self.drones = drones
		self.swarm_status = _coop.swarm_status
		self.state_ids = (0,1,2)

		# Assign pointers
		self.drone_controllers = drone_controllers # NB - actually a tuple of pointers
		self._coop = _coop
	
	def update(self,status):
		self.swarm_status = status
	
	def check_exit(self):
		"""
		Check the exit conditions against the state_properties.
		If state requires changing then do so to the correct state.
		"""
		# Ensure up-to-date status is held
		print "status update"
		self.update_status()

		# Check exit condition for each state against all exit conditions for the respective state
		for state in self.state_ids:
			for key in self.exit_conditions[state].keys():
				#print ("checking condition against: %s" % key)
				#print ("comparisson: %s" % ([self.exit_conditions[state][key],self.state_properties[key]]))
				if self.exit_conditions[state][key] == self.state_properties[key]:
					self.next_state(state)
					return

	def next_state(self,state_id):
		if state_id == 0:
			self._coop.change_state(SetupState(self._coop,self.drones,self.drone_controllers))
		elif state_id == 1:
			self._coop.change_state(TaskBad(self._coop,self.drones,self.drone_controllers))
		elif state_id == 2:
			self._coop.change_state(TaskGood(self._coop,self.drones,self.drone_controllers))
		
	def action(self):
		pass

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

		print("======In Setup State======")
	
	def action(self):
		# Check for change in drone status
		self._coop.start_drones()

			
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
	airprox == False && marker_following == True

	"""
	
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {}, {'airprox':False, 'marker_following':True}]

		print("======Task not being achieved======")
		self.action()
		
	def action(self):
		# Get route for drones
		new_routes = self._coop._navigator.route(self.state_properties['position'])
		print("new routes: %s" %new_routes)
		self._coop.send_routes(new_routes)
		
 
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
	airprox == True || marker_following == False

	State 2:
	-
	"""
	def __init__(self,_coop,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drones,drone_controllers)
		
		# Set exit conditions
		self.exit_conditions = [{}, {'airprox':True, 'following_marker':False}, {}]

		print("======Task being achieved======")
	
	def action(self):
		# Do nothing
		pass
