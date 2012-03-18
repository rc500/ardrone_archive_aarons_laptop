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
	A class which determines states of a drone.
	This is the base class from which all states inherit.
	As status messages are received, the state machine determines the next state and changes it accordingly.
	
	drone_properties =
					{
					'talking': False
					'airborne': False
					'height_stable':False
					# etc.
					}
	"""

	def __init__(self,_drone,drone_id):
		
		# Variables
		
		self.drone_properties = {
							'talking':False,
							'airborne':False,
							'height_stable':False,
							};
		self.drone_id = drone_id

		# Assign pointers
		self._drone = _drone
		
	def parse_status(self,status):
		"""
		When given a new status, parse the information and update the state properties.
		"""
		# Pop drone id
		status.pop('drone_id')

		# Update state properties
		self.drone_properties = status
		
	def check_exit(self):
		"""
		Check the exit conditions against the state_properties.
		If state requires changing, return the new state id.
		"""
		print "foo"
		# Ensure status is up to date
		self.parse_status(self._drone.update_status())

		exit_state = []
		#print ("Checking exit conditions %s against properties %s" % (self.exit_conditions,self.drone_properties))
		# Check exit conditions
		exit_state.append(False) # Initialise a bool for each drone
		for key in self.exit_conditions.keys():
			if self.exit_conditions[key] == self.drone_properties[key]:
				exit_state = True # Set flag for respective drone
			else:
				exit_state = False # Set flag for respective drone	
					
		# Only change state is all exit conditions have been met
		if exit_state == True:
			self._drone.change_state(self.next_state())
	
	def next_state(self):
		# Be sure to return pointer to next state
		pass
		
	def action(self):
		pass

class CommunicationState(State):
	"""
	ID = 0
	
	The state for when the drones are not verified as being in contact with the network.
	State entry requirements: -
	State purpose: to get drones communicating
	State exit: when drones are on and communicating
	
	State exit conditions:
		talking == True
	"""
		
	def __init__(self,_drone,drone_id):
		# Initialise as per State base class
		State.__init__(self,_drone,drone_id)

		# Set exit conditions (same for each drones)
		self.exit_conditions = {}
		self.exit_conditions['talking']=True
		
	def next_state(self):
		# Create next state
		return GroundState(self._drone,self.drone_id)
	
	def action(self):
		# Check for change in drone status
		print("--%s--In Communication State--%s--" % (self.drone_id,self.drone_id))
		pass
	
class GroundState(State):
	"""
	ID = 1
	
	The state for when the drones are not airborne.
	State entry requirements: drones are on and able to communicate with the controller.
	State purpose: to get drones airborne
	State exit: when drones are airborne
	
	State exit conditions:
		airborne == True for all drones
	"""

	def __init__(self,_drone,drone_id):
		# Initialise as per State base class
		State.__init__(self,_drone,drone_id)
		
		# Set exit conditions (same for each drones)
		self.exit_conditions = {}
		self.exit_conditions['airborne']=True

		# Setup timer to enable repeated attempts to reset and take off the drones at given intervals
		self.reset_timer = QtCore.QTimer()
		self.reset_timer.setInterval(6000) # ms
		self.reset_timer.timeout.connect(self.reset)
		
		self.takeoff_timer = QtCore.QTimer()
		self.takeoff_timer.setInterval(2000) # ms
		self.takeoff_timer.timeout.connect(self.take_off)

		self.action()

	def next_state(self):
		# Create next state
		return AirborneState(self._drone,self.drone_id)
		
	def action(self):
		# Start trying to take off drones
		print("--%s--In Ground State--%s--" % (self.drone_id,self.drone_id))
		self.reset_timer.start()
		
	def reset(self):
		print("beat-reset")
		# Reset then try to take off
		if self._drone.current_state['altitude'] < 30.0:
			self._drone.reset()
		self.reset_timer.stop()
		self.takeoff_timer.start()
		
	def take_off(self):
		print("beat-takeoff")
		# Try to take off then reset (should be enough delay before reset for state to exit if take off actually works)
		self._drone.take_off()
		self.takeoff_timer.stop()
		self.reset_timer.start()

class AirborneState(State):
	"""
	ID = 2
	
	The state for when the drones are initially airborne.
	State entry requirements: drones are airborne.
	State purpose: to get drones hovering stably at height.
	State exit: when drones are stable and ready to manoeuvre
	
	State exit conditions:
		height_stable == True for all drones
	"""

	def __init__(self,_drone,drone_id):
		# Initialise as per State base class
		State.__init__(self,_drone,drone_id)

		# Set exit conditions (same for each drones)
		self.exit_conditions = {}
		self.exit_conditions['height_stable']=True

		self.action()
				
	def next_state(self):
		# Create next state
		return ControlledState(self._drone,self.drone_id)
		
	def action(self):
		# Start trying to stablise the drones' height
		print("--%s--In Airborne State--%s--" % (self.drone_id,self.drone_id))
		self._drone.set_altitude(1000)

class ControlledState(State):
	"""
	ID = 3
	
	The state for when the drones are stable in height.
	State entry requirements: drones are stable at altitude.
	State purpose: to get drones hovering stably over target marker, transitioning through marker transition vector to achieve this.
	State exit: when marker is stable over target marker.
	
	State exit conditions:
		completed marker transition
	"""

	def __init__(self,_drone,drone_id):
		# Initialise as per State base class
		State.__init__(self,_drone,self.drone_id)

		# Set exit conditions (same for each drones)
		self.exit_conditions = {}
		self.exit_conditions['airborne']=False

		# Setup timer to look for next marker every so often
		self.look_timer = QtCore.QTimer()
		self.look_timer.setInterval(1000) # ms
		self.look_timer.timeout.connect(self.look)

		# Grab current route
		self.marker_transition = list(self._drone.route)

		self.action()

	def next_state(self):
		# Create next state
		print "----Finished Marker Transition----"
	
	def action(self):
		# Stablise the drone over a marker
		print("--%s--In Controlled State--%s--" % (self.drone_id,self.drone_id))

		# Start timer to look for next markers
		self.look_timer.start()

	def hold_marker(self,marker_id):
		print ("holding marker: %s" % marker_id)
		self._drone.hold_marker(marker_id)

	def look(self):
		# Check to see whether drones can see their next marker
		marker_id = self.pop_marker()
		if marker_id == None:
			return
		if (str(marker_id) in self._drone.get_visible_markers()):
			self.hold_marker(marker_id)
		else:
			self.add_marker(marker_id)
	
	def add_marker(self,marker_id):
		# Add a marker id into the transition vector
		self.marker_transition.append(marker_id)

	def pop_marker(self):
		# Pop the next marker from transition vector if such an element exists
		if not self.marker_transition:
			return None
		return self.marker_transition.pop()			
	
