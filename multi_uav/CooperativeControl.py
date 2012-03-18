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

from . import TaskStates as State

class CooperativeControl(object):

	def __init__(self,drones,drone_controllers): # Will want to add in _drone2 in time
		# --- STORE VARIABLES ---
		self.drones = drones # tuple of drone ids
		
		# --- STORE POINTERS ---
		self.drone_controllers = drone_controllers
	
		# --- INITIALISE APPLICATION OBJECTS ----
		#self._status_viewer = # add at some point
		self._network = NetworkManager(self)

		# Start program
		self.start()

	def start_drones(self):
		for drone in self.drone_controllers:
			drone.start()
		
	def start(self):
		print("======Program started======")
		# First state
		self._state = State.SetupState(self,self.drones,self.drone_controllers)
		self._state.action()
				
	def change_state(self,_state):
		"""
		Function called to update the state used by the CooperativeController object
		"""
		self._state = _state

	def parse_status(self,pulled_status):
		"""
		Parse the pulled status, return the resulting task status.
		"""
		task_status = {}

		# talking - only True if True for all drones
		task_status['talking'] = True
		for drone in self.drone_controllers:
			task_status['talking'] = task_status['talking'] and pulled_status[drone]['talking']

		# following_marker - only True if True for all drones
		task_status['following_marker'] = True
		for drone in self.drone_controllers:
			task_status['following_marker'] = task_status['following_marker'] and pulled_status[drone]['following_marker']

		# position - list of all drone positions
		task_status['position'] = []
		for drone in self.drone_controllers:
			task_status['position'].append(pulled_status[drone]['position'])

		# airprox - True if closer than 5 markers
		airprox = 5
		# work out shortest distance between drones
		closest_dist = 1000 # arbitrarily largei
		drone_count = 0
		other_count = 0
		for drone in self.drones:
			others = self.drones
			others = others.remove(drone)
			for other in others:
				diff_dist = task_status['position'][drone_count] - task_status['position'][other_count]
				if diff_dist < closest_dist:
					closest_dist = diff_dist
				other_count = other_count + 1
			drone_count = drone_count + 1
		# check distance with airprox
		if closest_dist >= airprox:
			task_status['airprox']=True
		else:
			task_status['airprox']=False

		return task_status

	def update_status():
		"""
		Request all drones to update their status.
		Return task status.
		"""
		pulled_status = []
		for drone in self.drone_controllers:
			pulled_status.append(drone.update_status())
		return self.parse_status(pulled_status)

	def send_routes(self,routes):
		"""
		Function which gives each drone a route in the form of a list of marker ids.
		"""
		local_drone = list(self.drone_controllers)
		local_drone.reverse()

		for route in routes:
			local_drone.pop().update_route(route)

	def operation(self):
		"""
		Carry out the next required action.
		"""
		self._state.action()

class Navigator(object):
	"""
	A class which works out safe routes for drones to follow.
	All functions are called with a list of the drones current positions (and possibly other parameters too)
	All 'public' functions return one list of n lists, where n is the number of drones being controlled
	"""

# PUBLIC
	def __init__(self,drones):
		# define map
		self.path = {
			'type' : 'loop',
			'markers' : (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24),
			};

		# setup variables
		self.routes = [] # one route for each drone being controlled
		for number in drones:
			self.routes.append([])

		self.positions = [] # one marker id for each drone giving last known position
		self.targets = [] # 0 or 1  marker id for each drone giving the current target for the drone
		self.drones = drones # tuple of drone ids

	def route (self,pos):
		"""
		A basic algorithm for setting a looping route around a continuous path. Route is never longer than 6 markers ahead.
		"""
		# check path is a loop
		if self.path['type'] == 'loop':
			for drone in self.drones:
				posi = pos[drone]
				self.routes[drone] = [posi]
				for number in range(1,6):
					posi = self.next(posi)
					self.routes[drone].append(posi)

		# return deconflicted routes
		return self.deconflict(self,self.positions)

	def deconflict(self,pos):
		"""
		A basic deconfliction algorithm which stops all drones that have unsafe routes
		Only guarantees deconfliction on maps with no junctions
		"""
		# update position
		self.position = pos

		# work out new routes to deconflict drones while maintaining efficient routing to targets
		# check safety of current routes
		safe_routes = self.check_rvp()
		# for unsafe routes, stop the drone
		for drone in safe_route:
			if drone == False:
				self.routes[drone] = self.positions[drone] # halt the drone
	
		return self.routes

# PRIVATE
	def check_rvp(self):
		"""
		Checks the routes of each drone with the current position of the other drones.
		A list containing bools is returned.
		If a route risks collision with another drone then False is returned for that drone.
		""" 
		safe_route = []
		for drone in self.drones:
			safe_route.append(True)
			others = self.drones
			others.remove(drone)
			for other in others:
				if self.positions[other] in self.routes[drone]:
					safe_route[drone] = False
		return safe_route

	def next(self,pos):
		"""
		Returns markers next to current marker in order [forward,backward]
		"""
		if self.path['type'] == loop:
			local_path = list(self.path['markers'])
			if pos == local_path[len(local_path)]: # if current position is last position in markers tuple
				backward = local_path[local_path.index(pos)-1]
				forward = local_path.reverse().pop()
			elif pos == local_path[1]: # if current position is the first position in markers tuple
				forward = local_path[2]
				backward = local_path.pop()
			else:
				forward = local_path[local_path.index(pos)+1]
				backward = local_path[local_path.index(pos)-1]

		return [forward,backward]
			
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
		
	def readStatusData_pseudo(self,data):
		# Call CooperativeControl with status message if it is a dictionary data structure
		if type(data)==type({}):
			self._coop.update(data)
		else:
			print("rogue status message received")
			

