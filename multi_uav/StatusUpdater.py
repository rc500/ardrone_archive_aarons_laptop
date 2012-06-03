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
	Expand documentation here - e.g. contents of statuses
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
					'vbat_flying_percentage':0,
					};

		initial_drone_status = {
					'type': 'drone',
					'talking':False,
					'airborne':False,
					'height_stable':False,
					'position':-1,
					'following_marker':False,
					'battery':0,
					};

		self.swarm_status = {
					'type': 'swarm',
					'position':[],
					'talking':False,
					'height_stable':False,
					'following_marker':False,
					'airprox':False,
					'observing_target':False,
					'observer':-1,
					'battery':[],
					};		

		self.drone_status = []
		for count in self.drones:
			self.drone_status.append(initial_drone_status) 

		# Push initial statuses
		for drone in self.drones:
			initial_drone_status['drone_id'] = drone
			initial_raw_status['drone_id'] = drone
			self.push_drone_status(initial_raw_status)
			self.push_drone_status(initial_drone_status)
		self.push_swarm_status(self.swarm_status)

	def update(self,status):
		"""
		Take status (dictionary structure) and parse given status to propagate up levels (raw->drone->swarm)
		Only raw statuses should be passed into the class - all others will be rejected
		"""

		#print(status)

		# Parse and push all raw and drone statuses to DroneControl
		if status['type'] == 'raw':
			# Parse raw status
			_drone_status = self.parse_raw_for_drone(status)
			# Update local version of drone_status
			self.drone_status[self.drones.index(status['drone_id'])] = _drone_status
			# Push out statuses
			self.push_drone_status(_drone_status)
			# Update and push swarm status
			self.parse_drone_for_swarm()
			self.push_swarm_status(self.swarm_status)

		else:
			print("non-raw status passed - StatusUpdater")

	def push_drone_status(self,status):
		"""
		Pushes status message to appropriate DroneControl
		"""
		drone_id = status['drone_id']
		if status['type'] == 'raw':
			self.drone_controllers[self.drones.index(drone_id)].update_raw(status)
		if status['type'] == 'drone':
			self.drone_controllers[self.drones.index(drone_id)].update_drone(status)
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

	def parse_drone_for_swarm(self):
		"""
		Parse drone status into format for swarm status.
		This takes the current swarm_status and updates it.
		"""
		# talking - only True if True for all drones
		self.swarm_status['talking'] = True
		for drone in range(0,len(self.drones)):
			self.swarm_status['talking'] = self.swarm_status['talking'] and self.drone_status[drone]['talking']

		# following_marker - only True if True for all drones
		self.swarm_status['following_marker'] = True
		for drone in range(0,len(self.drones)):
			self.swarm_status['following_marker'] = self.swarm_status['following_marker'] and self.drone_status[drone]['following_marker']

		# height_stable - only True if True for all drones

		self.swarm_status['height_stable'] = True
		for drone in range(0,len(self.drones)):
			self.swarm_status['height_stable'] = self.swarm_status['height_stable'] and self.drone_status[drone]['height_stable']

		# position - list of all drone positions. 
		self.swarm_status['position'] = []
		for drone in range(0,len(self.drones)):
			self.swarm_status['position'].append(self.drone_status[drone]['position'])

		# airprox - shortest distance between drones
		# work out shortest distance between drones
		closest_dist = self._swarm_controller.min_separation
		# check distance with airprox
		if closest_dist < 9:
			self.swarm_status['airprox'] = True
		else:
			self.swarm_status['airprox'] = False

		# separation
		self.swarm_status['separation'] = closest_dist

		# observing_target (target = marker 0)
		self.swarm_status['observing_target'] = False
		for drone in range(0,len(self.drones)):
			if self.drone_status[drone]['position'] == 0:
				self.swarm_status['observing_target'] = True

		# observer (drone_id of drone who is over marker 0) (-1 if no drone is observing)
		self.swarm_status['observer'] = -1
		for drone in range(0,len(self.drones)):
			if self.drone_status[drone]['position'] == 0:
				self.swarm_status['observer'] = self.drones[drone]

		# battery
		self.swarm_status['battery'] = []
		for drone in range(0,len(self.drones)):
			self.swarm_status['battery'].append(self.drone_status[drone]['battery'])

	def parse_raw_for_drone(self,status):
		"""
		Parse raw status into format for drone status
		"""

		# work out useful information
		drone_id = status['drone_id']
		drone_controller = self.drone_controllers[self.drones.index(drone_id)]

		# drone_id
		drone_status = {'drone_id':drone_id}
	
		# assign type
		drone_status['type'] = 'drone'

		# talking
		drone_status['talking'] = drone_controller.control_network_activity_flag and drone_controller.video_network_activity_flag
	
		# airborne
		if status['altitude'] >= 270.0:
			drone_status['airborne'] = True
		else:
			drone_status['airborne'] = False
		#print (self.status['altitude'])
	
		# height_stable
		drone_status['height_stable'] = drone_controller.stability_info['gas_stable']

		# following_marker
		if len(drone_controller.route) > 1: # drone with routes of length 1 are not following a marker 
			drone_status['following_marker'] = True
		else:
			drone_status['following_marker'] = False

		# position (marker_id)
		# currently tracked marker. If position is -1 and drone is not airborne, take its position to be its home position
		if status['marker_id'] == -1:
			visible = drone_controller.get_visible_markers()
			#print ("visible: %s" %visible)
			if not visible and self.drone_controllers[self.drones.index(drone_id)].state_id < 1:
				drone_status['position'] = self.drone_controllers[self.drones.index(drone_id)].home
			elif not visible:
				drone_status['position'] = -1
			else:	
				drone_status['position'] = int(visible[0])
		else:
			drone_status['position'] = status['marker_id']

		# battery (if simulation is ON, and this drone is the observer, then set battery to a low %)
		if self._swarm_controller.simulate_flag == False or not drone_id == self.swarm_status['observer']:
			drone_status['battery'] = status['vbat_flying_percentage']
		else:
			if drone_id == self.swarm_status['observer']:
				drone_status['battery'] = 10

		# Update status
		#print ("Sending state : %s" % drone_status)
		return drone_status
