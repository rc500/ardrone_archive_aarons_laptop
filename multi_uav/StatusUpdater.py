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

class StatusUpdater(object):
	"""
	Updates statuses through code, parsing into the required format at each stage.

	Different levels of abstraction for statuses:
		- swarm_status 
		- drone_status
		- raw_status
	"""

	def __init__(self,drones,drone_controllers,swarm_controller):
		"""
		Initialises the StatusUpdater with pointers to inidividual DroneController s and SwarmController
		Pushes initial statuses to application
		"""
		# Assign tuples and pointer
		self.drones = drones
		self.drone_controllers = drone_controllers
		self._swarm_controller = swarm_controller

		# Push out initial statuses to objects
		initial_raw_status = {
					'type': 'raw',
					'drone_id' : 0,
					'marker_id': -1,
					'marker_distance_x': 0.0,
					'marker_distance_y': 0.0,
					'gas_stable' : False,
					'roll_stable' : True, # dirty
					'pitch_stable' : True, # dirty
					'altitude' : 0.0,
					};

		initial_drone_status = {
					'type': 'drone',
					'talking':False,
					'airborne':False,
					'height_stable':False,
					};

		initial_swarm_status = {
					'type': 'swarm',
					'position':[],
					'talking':False,
					'height_stable':False,
					};		

		self.push_drone_status(initial_raw_status)
		self.push_drone_status(initial_drone_status)
		self.push_drone_state_status(initial_drone_status)
		self.push_swarm_status(initial_swarm_status)
		self.push_swarm_state_status(initial_swarm_status)

	def update(self,status):
		"""
		Take status (dictionary structure) and parse given status to propagate up levels (raw->drone->swarm)

		Allows both raw and drone status to be parsed up, however it is recommended that only raw statuses are fed in from outside the class
		"""

		# Push all raw statuses to DroneControl, parse and push all raw statuses to DroneState
		if status['type'] == 'raw':
			# Parse raw status
			parsed_status = self.parse_raw_for_drone(status)
			# Push out statuses
			self.push_drone_status(status)
			self.push_drone_status(parsed_status)
			self.push_drone_state_status(parsed_status)
			# Recursively call update to push up to swarm level
			self.update(parsed_status)

		# Parse and push all drone statuses to SwarmControl
		if status['type'] == 'drone':
			parsed_status = self.parse_drone_for_swarm(status)
			self.push_swarm_status(parsed_status)
			self.push_swarm_state_status(parsed_status)

	def push_drone_status(self,status):
		"""
		Pushes status message to DroneControl
		"""
		if status['type'] == 'raw':
			for index in range (0,len(self.drones)):
				status['drone_id']=self.drones[index]
				self.drone_controllers[index].update_raw(status)
		if status['type'] == 'drone':
			for index in range (0,len(self.drones)):
				status['drone_id']=self.drones[index]
				self.drone_controllers[index].update_drone(status)
		if status['type'] == 'swarm':
			print ("StatusUpdater - push_status error - status of given type should not be sent to given destination")

	def push_drone_state_status(self,status):
		"""
		Pushes status message to DroneState
		"""
		if status['type'] == 'raw':
			print ("StatusUpdater - push_status error - status of given type should not be sent to given destination")
		if status['type'] == 'drone':
			for index in range (0,len(self.drones)):
				status['drone_id']=self.drones[index]
				self.drone_controllers[index]._state.update(status)
		if status['type'] == 'swarm':
			print ("StatusUpdater - push_status error - status of given type should not be sent to given destination")

	def push_swarm_status(self,status):
		"""
		Pushes status message to SwarmControl
		"""
		if status['type'] == 'raw':
			print ("StatusUpdater - push_status error - status of given type should not be sent to given destination")
		if status['type'] == 'drone':
			print ("StatusUpdater - push_status error - status of given type should not be sent to given destination")
		if status['type'] == 'swarm':
			self._swarm_controller.update(status)

	def push_swarm_state_status(self,status):
		"""
		Pushes status message to SwarmState
		"""
		if status['type'] == 'raw':
			print ("StatusUpdater - push_status error - status of given type should not be sent to given destination")
		if status['type'] == 'drone':
			print ("StatusUpdater - push_status error - status of given type should not be sent to given destination")
		if status['type'] == 'swarm':
			self._swarm_controller._state.update(status)

	def parse_drone_for_swarm(self,status):
		"""
		Parse drone status into format for swarm status
		"""
		swarm_status = {}

		# talking - only True if True for all drones
		swarm_status['talking'] = True
		for drone in range(0,len(self.drones)):
			swarm_status['talking'] = swarm_status['talking'] and status[drone]['talking']

		# following_marker - only True if True for all drones
		swarm_status['following_marker'] = True
		for drone in range(0,len(self.drones)):
			swarm_status['following_marker'] = swarm_status['following_marker'] and status[drone]['following_marker']

		# height_stable - only True if True for all drones

		swarm_status['height_stable'] = True
		for drone in range(0,len(self.drones)):
			swarm_status['height_stable'] = swarm_status['height_stable'] and status[drone]['height_stable']

		# position - list of all drone positions
		swarm_status['position'] = []
		for drone in range(0,len(self.drones)):
			swarm_status['position'].append(status[drone]['position'])

		# airprox - True if closer than 5 markers
		airprox = 5
		# work out shortest distance between drones
		closest_dist = 1000 # arbitrarily large
		drone_index = []
		other_index = []
		d_count = 0
		for drone in self.drones:
			drone_index.append(d_count)
			other_index.append(d_count)
			d_count = d_count + 1
		for drone in drone_index:
			others = list(self.drones)
			other_index.remove(others.index(self.drones[drone]))
			for other in other_index:
				diff_dist = swarm_status['position'][drone] - swarm_status['position'][other]
				if diff_dist < closest_dist:
					closest_dist = diff_dist
			other_index.append(others.index(self.drones[drone]))
		# check distance with airprox
		if closest_dist <= airprox:
			swarm_status['airprox']=True
		else:
			swarm_status['airprox']=False

		return swarm_status
				
	def parse_raw_for_drone(self,status):
		"""
		Parse raw status into format for drone status
		"""

		# drone_id
		drone_status = {'drone_id':self.status['drone_id']}
	
		# talking
		drone_status['talking'] = self.control_network_activity_flag and self.video_network_activity_flag
		
		# airborne
		if self.status['altitude'] >= 270.0:
			drone_status['airborne'] = True
		else:
			drone_status['airborne'] = False
		#print (self.status['altitude'])
	
		# height_stable
		drone_status['height_stable'] = self.status['gas_stable']
		
		# following_marker
		if len(self.route)>1:
			drone_status['following_marker'] = True
		else:
			drone_status['following_marker'] = False

		if self.holding_marker == False:
			drone_status['following_marker'] = False

		# position (marker_id)
		# currently tracked marker
		if self.status['marker_id'] == -1:
			visible = self.get_visible_markers()
			#print ("visible: %s" %visible)
			if not visible:
				drone_status['position'] = -1
			else:	
				drone_status['position'] = int(visible[0])
		else:
			drone_status['position'] = self.status['marker_id']

		# Update status
		#print ("Sending state : %s" % drone_status)
		return drone_status
