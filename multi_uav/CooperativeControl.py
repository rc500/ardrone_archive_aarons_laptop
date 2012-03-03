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

class CooperativeControl(object):

	def __init__(self,drones,drone_controllers): # Will want to add in _drone2 in time
		# --- STORE VARIABLES ---
		self.drones = drones # tuple of drone ids
		
		# --- INITIALISE APPLICATION OBJECTS ----
		#self._status_viewer = # add at some point
		self._network = NetworkManager(self)
		
		# First state
		self._state = CommunicationState(self,drone_controllers)
		
		# Start program
		self.start()
		
	def start(self):
		print("----Program started----")
		self.operation()
		
	def update(self,status):
		"""
		Update the state object and check whether the state should change.
		"""
		# Update state object
		self._state.update(status)
		
		# Change state if required to
		check = self._state.check_exit()
		if check[0] == False:
			return
		else:
			print("Changing State")
			self._state = check[1]
			self.operation()

	def operation(self):
		"""
		Carry out the next required action.
		"""
		self._state.action()

class State(object):
	"""
	A class which manages the state of the CooperativeController object.
	This is the base class from which all states inherit.
	As status messages are received, the state machine determines the next state and changes it accordingly.
	
	drone_properties =
					{
					'talking': False
					'airborne': False
					'height_stable':False
					# etc.
					}
					
	state_properties = [#drone1_properties,drone2_properties,...]
	"""

	def __init__(self,_coop,drone_controllers):
		
		# Variables
		self.drone_properties = {
							'talking':False,
							'airborne':False,
							'height_stable':False,
							};
		
		self.state_properties = [] # [{drone1},{drone2},...]
		for count in drone_controllers:
			self.state_properties.append(self.drone_properties)

		# Assign pointers
		self.drone_controllers = drone_controllers # NB - actually a tuple of pointers
		self._coop = _coop
		
	def update(self,status):
		"""
		When given a new status, parse the information and update the state properties.
		"""
		# Store drone_id and remove it
		drone_id = status.pop('drone_id')

		# Update state properties
		self.state_properties[drone_id - 1] = status
		#rint("update readout:")
		#print(status,self.state_properties)
		
	def check_exit(self):
		"""
		Check the exit conditions against the state_properties.
		If state requires changing, return the new state id.
		"""
		exit_state = []
		
		# Check exit condition
		for drone_id in self._coop.drones:
			exit_state.append(False) # Initialise a bool for each drone
			#print("Drone: %s" %drone_id)
			for key in self.exit_conditions[drone_id-1].keys():
				#print("Property: '%s'" %key)
				#print(self.state_properties)
				#print(self.exit_conditions[drone_id-1][key],self.state_properties[drone_id-1][key])
				if self.exit_conditions[drone_id-1][key] == self.state_properties[drone_id-1][key]:
					exit_state[drone_id-1] = True # Set flag for respective drone
				else:
					exit_state[drone_id-1] = False # Set flag for respective drone	
					#return (False,) # Leave loop as don't care about meeting rest of conditions
					
		# Only change state is all exit conditions have been met
		exit_state.sort()
		if exit_state[0] == True: # Don't actually need this line and line above
			print("Exiting State")
			return (True,self.next_state())
		return (False,)
	
	def next_state(self):
		# Be sure to return pointer to next state
		pass
		
	def action(self):
		pass

class CommunicationState(State):
	"""
	ID = 0
	
	The CommunicationState for when the drones are not verified as being in contact with the network.
	State entry requirements: -
	State purpose: to get drones communicating
	State exit: when drones are on and communicating
	
	State exit conditions:
		talking == True
	"""
		
	def __init__(self,_coop,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,_coop,drone_controllers)

		# Set exit conditions (same for each drones)
		self.exit_conditions = []
		for count in drone_controllers:
			self.exit_conditions.append ({'talking':True})

		# Setup timer to enable repeated checks of drone communication status
		self.check_timer = QtCore.QTimer()
		self.check_timer.setInterval(1000) # ms
		self.check_timer.timeout.connect(self.check)
		
	def next_state(self):
		# Create next state
		return GroundState(self._coop,self.drone_controllers)
	
	def action(self):
		# Check for change in drone status
		print("----In Communication State----")
		self.check_timer.start()
	
	def check(self):
		# Update status of drones
		for drone in self.drone_controllers:
			drone.update_status()
			
class GroundState(State):
	"""
	ID = 1
	
	The GroundState state for when the drones are not airborne.
	State entry requirements: drones are on and able to communicate with the controller.
	State purpose: to get drones airborne
	State exit: when drones are airborne
	
	State exit conditions:
		airborne == True for all drones
	"""

	def __init__(self,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,drones,drone_controllers)
		
		# Set exit conditions (same for each drones)
		self.exit_conditions = []
		for count in drone_controllers:
			self.exit_conditions.append ({'airborne':True})

		# Setup timer to enable repeated attempts to reset and take off the drones at given intervals
		self.reset_timer = QtCore.QTimer()
		self.reset_timer.setInterval(1000) # ms
		self.reset_timer.timeout.connect(self.reset)
		
		self.takeoff_timer = QtCore.QTimer()
		self.takeoff_timer.setInterval(1000) # ms
		self.takeoff_timer.timeout.connect(self.take_off)

		self.check_timer = QtCore.QTimer()
		self.check_timer.setInterval(6000) # ms
		self.check_timer.timeout.connect(self.check)

	def next_state(self):
		# Create next state
		return HoverState(self._coop,self.drone_controllers)
		
	def action(self):
		# Start trying to take off drones
		print("----In Ground State----")
		self.reset_timer.start()
		
	def reset(self):
		print("beat-reset")
		# Reset then try to take off
		for drone in self.drone_controllers:
			if drone.current_state['altitude'] < 100.0:
				drone.reset()
		self.reset_timer.stop()
		self.takeoff_timer.start()
		
	def take_off(self):
		print("beat-takeoff")
		# Try to take off then reset (should be enough delay before reset for state to exit if take off actually works)
		for drone in self.drone_controllers:
			drone.take_off()
		self.takeoff_timer.stop()
		self.check_timer.start()

	def check(self):
		print("beat-check")
		# Check state
		for drone in self.drone_controllers:
			drone.update_status()
		self.check_timer.stop()
		self.reset_timer.start()

class HoverState(State):
	"""
	ID = 2
	
	The CooperativeController state for when the drones are initially airborne.
	State entry requirements: drones are airborne.
	State purpose: to get drones hovering stably at height.
	State exit: when drones are stable and ready to manoeuvre
	
	State exit conditions:
		height_stable == True for all drones
	"""

	def __init__(self,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,drones,drone_controllers)

		# Set exit conditions (same for each drones)
		self.exit_conditions = []
		for count in drone_controllers:
			self.exit_conditions.append ({'height_stable':True})
				
	def next_state(self):
		# Create next state
		return MarkerState(self._coop,self.drone_controllers)
		
	def action(self):
		# Start trying to stablise the drones' height
		print("----In Hover State----")
		for drone in self.drone_controllers:
			drone.set_altitude(1000)

class MarkerState(State):
	"""
	ID = 3
	
	The CooperativeController state for when the drones are stable in height.
	State entry requirements: drones are stable at altitude.
	State purpose: to get drones hovering stably over a marker.
	State exit: when drones are stable and ready to manoeuvre
	
	State exit conditions:
		above_marker == True for all drones
	"""

	def __init__(self,drones,drone_controllers):
		# Initialise as per State base class
		State.__init__(self,drones,drone_controllers)

		# Set exit conditions (same for each drones)
		self.exit_conditions = []
		for count in drone_controllers:
			self.exit_conditions.append ({'airborne':False})

	def next_state(self):
		# Create next state
		return MarkerState(self._coop,self.drone_controllers)
		
	def action(self):
		# Stablise the drone over a marker
		print("----In Marker State----")
		for drone in self.drone_controllers:
			drone.hold_marker()
					
class NetworkManager(object):
	"""
	A class which manages the sending and receiving of packets over the network.
	It stores the relevant data of received packets and sends packets when requested.
	
	IP address of drone: config.['host']
	Localhost: 127.0.0.1
	"""
	
	
	def __init__(self,initialiser):
		"""
		Initialise the class
		"""
		self._coop = initialiser
		
		# Set up a UDP listening socket on port for status data
#		self.socket_status = QtNetwork.QUdpSocket()
#		if not self.socket_status.bind(QtNetwork.QHostAddress.Any, self.PORT_STATUS):
#			raise RuntimeError('Error binding to port: %s' % (self.socket_status.errorString()))
#		self.socket_status.readyRead.connect(self.readStatusData)

	def readStatusData_pseudo(self,data):
		# Call CooperativeControl with status message if it is a dictionary data structure
		if type(data)==type({}):
			self._coop.update(data)
		else:
			print("rogue status message received")
			
	#def readStatusData(self):
		#"""
		#Called when there is some interesting data to read on the status socket.
		#The status message is passed onto CooperativeControl object for processing.
		#"""
		#while self.socket_status.hasPendingDatagrams():
			#sz = self.socket_status.pendingDatagramSize()
			#(data, host, port) = self.socket_status.readDatagram(sz)
	
			## Call CooperativeControl with status message if it is a dictionary data structure
			#if type(data)==type({}):
				#self._coop.update(data)
			#else:
				#print("rogue status message received")
