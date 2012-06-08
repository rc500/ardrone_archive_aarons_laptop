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
	A class which takes drone positions and returns lists of drone routes which are safe to take.

	When Navigating multiple drones at once:
	All functions are called with a list of the drones' current positions (and possibly other parameters too)
	All 'public' functions return one list of n lists, where n is the number of drones being controlled, and the list contains a route
	The route list must be in the order:
		element 0 in list = last marker on route
		last element in list = next marker to go to

	Routes should not contain the present marker
	"""

# PUBLIC
	def __init__(self,drones,initial_positions):
		# define map
		self.path = {
			'type' : 'line',
			'markers' : (25,26,27,28,29,30,31,32,33,34,35,0,)
			};

		# setup variables
		self.routes = [] # one route for each drone being controlled
		for number in drones:
			self.routes.append([])

		self.positions = initial_positions # one marker id for each drone giving last known position
		self.targets = [] # 0 or 1  marker id for each drone giving the current target for the drone
		for number in drones:	
			self.targets.append(-1)
	
		self.drones = drones # tuple of drone ids

	def route_to_target(self,pos,tgt,drone_id):
		"""
		Returns a route from pos to tgt ground references for a single drone. This route is deconflicted with other drone locations and routes.
		Current implementation only works for a straight line path.
		"""
		# store updated position
		self.positions[self.drones.index(drone_id)] = pos
		#print("current position: %s" % pos)

		# check not currently at target
		if pos == tgt:
			return_value = []
			for count in self.positions:
				return_value.append([-1])
			return return_value 

		# check position is known
		elif pos == -1:
			return_value = []
			for count in self.positions:
				return_value.append([-1])
			return return_value 

		# check position is in current mapping
		elif pos not in self.path['markers']:
			print("Error: Drone has location not on known path. Originator: Navigator")

		# check path is a line
		elif self.path['type'] == 'line':
			drone_index = self.drones.index(drone_id)
			# assume the route will be in one direction and create a route as such
			posi = pos
			direction = 0
			self.routes[drone_index] = []
			# check that tgt is in path
			if tgt not in self.path['markers']:
				print("Error - requested target is not in known path. Originator: Navigator")
			# check at each stage whether destination or end of line has been reached and discard or send route as appropriate
			while not self.next(posi)[direction] == tgt:
				# continue route
				self.routes[drone_index].append(self.next(posi)[direction])

				# check for end of path
				if self.routes[drone_index][len(self.routes[drone_index])-1] == -1:
					# reset route and position
					self.routes[drone_index] = []
					posi = pos
					# change direction
					direction = 1
				else:
					# update posi
					posi = self.next(posi)[direction]
			# when next position is the target (i.e. when while loop exits) finish the route, check for deconfliction and return it
			self.routes[drone_index].append(self.next(posi)[direction])
			# reverse route
			self.routes[drone_index].reverse()

			return self.check_deconflict(self.positions)
			

	def route(self,pos):
		"""
		A basic algorithm for returning a looping route for all drones around a continuous path. Route is never longer than 6 markers ahead.
		"""
		self.positions = pos
		# check position is known
		if -1 in pos:
			return_value = []
			for count in self.positions:
				return_value.append([-1])
			return return_value 
		# check position is in current mapping
		for location in pos:
			if location not in self.path['markers']:
				print("Error: Drone has location not on known path. Originator: Navigator")
				return
		# check path is a loop
		if self.path['type'] == 'loop':
			# for each drone
			for drone in range(0,len(self.drones)):
				# calculate the next marker in route
				posi = pos[drone]
				posi = self.next(posi)[0]
				self.routes[drone] = [posi,]
				# calculate remaining markers in route (up to 6 ahead)
				for number in range(1,6):
					posi = self.next(posi)[0]
					self.routes[drone].append(posi)
				self.routes[drone].reverse()

		# return deconflicted routes
		return self.check_deconflict(self.positions)

	def hold_position_route(self,pos):
		"""
		Returns a route which is the same as current positions passed (i.e. just turns a position into a route)

		"""
		self.positions = pos
		for drone in range(0,len(self.drones)):
			self.routes[drone] = [pos[drone],]
		return self.check_deconflict(self.positions)

	def front_drone(self):
		"""
		Returns drone_id of the drone in front of loop.
		'Front' drone is determined by whichever drone has the most number of clear spaces in front of them.
		"""
		# this will need updating but for now the front drone will always be drone with id 1
		return 2 

	def check_deconflict(self,pos):
		"""
		A basic deconfliction algorithm which changes the routes of all drones that have unsafe routes
		Only guarantees deconfliction on maps with no junctions
		"""
		# update position
		self.position = pos

		# work out new routes to deconflict drones while maintaining efficient routing to targets
		# check safety of current routes
		safe_routes = self.check_rvp()
		# for unsafe routes, change a drones route to prevent airprox
		for drone in safe_routes:
			if drone == False:
				self.routes[drone] = [self.positions[drone],]
		return self.routes

	def min_separation(self,pos):
		"""
		Returns integer which is the minimum separation between all positions provided
		Simple (inefficient) algorithm counts one way until reaching end of the line or another position, then does the same the other direction. Then do both these for every position. It takes the minimum value between positions.
		Algorithm could be optimized but for low number of drones it is sufficient.
		"""	
		self.positions = pos
		if self.path['type'] == 'line':
			# initial direction and starting position
			direction = 0
			separation = -1 

			# for each drone's position
			for index in range(0,len(self.drones)):
				# and for each direction
				for direction in range(0, 2):
					l_separation = 0
					posi = self.next(pos[index])[direction]
					# keep counting until reach another position or end of the line
					while posi not in pos and not posi == -1:
						posi = self.next(posi)[direction]
						l_separation = l_separation + 1
					# if reach end of line first, then do nothing
					if posi == -1:
						pass
					# if reach another position first, compare it to the current separation and replace if smaller (or the first)
					else:
						if l_separation < separation or separation == -1:
							separation = l_separation
			return separation
# PRIVATE
	def check_rvp(self):
		"""
		Checks the routes of each drone with the current position of the other drones.
		A list containing bools is returned.
		If a drone's route risks collision with another then False is returned for that drone.
		""" 
		safe_route = []
		drone_index = []
		d_count = 0

		# generate drone_index and other_index list
		for drone in self.drones:
			safe_route.append(True)
			others = list(self.drones)
			others.remove(drone)
			drone_index.append(d_count)
			d_count = d_count + 1
		other_index = drone_index

		# for each drone, check against all other drones
		for drone in drone_index:
			other_index.remove(drone)
			for other in other_index:
				if self.positions[other] in self.routes[drone]:
					safe_route[drone] = False
			other_index.append(drone)

		return safe_route

	def next(self,pos):
		"""
		Must be passed an integer position
		Returns a list of markers next to current marker in order [marker in front of,marker behind]
		Returns -1 if end of non-looping path
		"""
		local_path = list(self.path['markers'])

		if pos == local_path[len(local_path)-1]: # if current position is last position in markers tuple
			backward = local_path[local_path.index(pos)-1]
			if self.path['type'] == 'loop':
				local_path.reverse()
				forward = local_path.pop()
			else:
				forward = -1
		elif pos == local_path[0]: # if current position is the first position in markers tuple
			forward = local_path[1]
			if self.path['type'] == 'loop':
				backward = local_path.pop()
			else:
				backward = -1
		elif pos == -1:
			#print "no markers visible"
			forward = -1
			backward = -1
		else:
			forward = local_path[local_path.index(pos)+1]
			backward = local_path[local_path.index(pos)-1]
			
		return [forward,backward]
