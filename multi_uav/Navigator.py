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

# Import required application objects

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

	def route(self,pos):
		"""
		A basic algorithm for setting a looping route around a continuous path. Route is never longer than 6 markers ahead.
		"""
		self.positions = pos

		# check position is known
		if -1 in pos:
			return [[-1],[-1]]
		# check path is a loop
		if self.path['type'] == 'loop':
			for drone in range(0,len(self.drones)):
				posi = pos[drone]
				self.routes[drone] = [posi]
				for number in range(1,6):
					posi = self.next(posi)[0]
					self.routes[drone].append(posi)
			self.routes[drone].reverse()

		print("routes: %s" % self.routes)
		# return deconflicted routes
		return self.check_deconflict(self.positions)

	def check_deconflict(self,pos):
		"""
		A basic deconfliction algorithm which changes the routes of all drones that have unsafe routes
		Only guarantees deconfliction on maps with no junctions
		"""
## refactor - stop navigator controlling drones
		# update position
		self.position = pos

		# work out new routes to deconflict drones while maintaining efficient routing to targets
		# check safety of current routes
		safe_routes = self.check_rvp()
		# for unsafe routes, change a drones route to prevent airprox
		for drone in safe_routes:
			if drone == False:
				self.routes[drone] = self.positions[drone]
	
		return self.routes

# PRIVATE
	def check_rvp(self):
		"""
		Checks the routes of each drone with the current position of the other drones.
		A list containing bools is returned.
		If a route risks collision with another drone then False is returned for that drone.
		""" 
		safe_route = []
		drone_index = []
		d_count = 0
		for drone in self.drones:
			safe_route.append(True)
			others = list(self.drones)
			others.remove(drone)
			drone_index.append(d_count)
			d_count = d_count + 1
		other_index = drone_index
		for drone in drone_index:
			other_index.remove(drone)
			for other in other_index:
				if self.positions[other] in self.routes[drone]:
					safe_route[drone] = False
			other_index.append(drone)

		return safe_route

	def next(self,pos):
		"""
		Returns markers next to current marker in order [forward,backward]
		"""
		if self.path['type'] == 'loop':
			local_path = list(self.path['markers'])
			if pos == local_path[len(local_path)-1]: # if current position is last position in markers tuple
				backward = local_path[local_path.index(pos)-1]
				forward = local_path.reverse().pop()
			elif pos == local_path[1]: # if current position is the first position in markers tuple
				forward = local_path[2]
				backward = local_path.pop()
			elif pos == -1:
				print "no markers visible"
				forward = -1
				backward = -1
			else:
				forward = local_path[local_path.index(pos)+1]
				backward = local_path[local_path.index(pos)-1]
			
		return [forward,backward]
