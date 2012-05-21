import os
import sys
import json, socket, time

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')

from . import Controllers as Controller
from . import DroneStates as State
from . import ImageProcessor
import ardrone.core.videopacket as Videopacket

import logging 
#logging.basicConfig(level=logging.DEBUG)

class DroneControl(object):
	"""
	The base class for overseeing actions of an individual drone.
	
	Acts upon messages from SwarmControl class by changing position (using Controller class) or carrying out standard land, take off, change camera actions (using ControlLoop class).
	"""
	
	def __init__(self,drone_id,_control,network_config,updater):
		# --- INITIALISE VARIABLES ---
		self.raw_status = {};
		self.drone_status = {};
		self.drone_input = {
	                'roll': 0.0,
	                'pitch': 0.0,
	                'yaw': 0.0,
	                'gas': 0.0,
	                'take_off': False,
	                'reset': False,
	                'hover': True,
                     			};

		self.stability_info = {
			'gas_stable' : False,
			'roll_stable' : False,
			'pitch_stable' : False,
					};

		self.visible_marker_info = {
				#'marker_id': [x error,y error]
				'-1':(0,0),
				};			
	           
		self.control_network_activity_flag = False
		self.video_network_activity_flag = False

		self.holding_marker = False
		self.route = [-1,]
		self.drone_id = drone_id	
		
		# --- ASSIGN POINTERS ---
		self._control=_control
		self._updater=updater

		# Configure drone camera
		self._control.view_camera(1) # channel 1 = downward facing camera
		
		# --- INITIALISE APPLICATION OBJECTS ----
		self._im_proc = ImageProcessor.ImageProcessor(self,drone_id)
		self._vid_decoder = Videopacket.Decoder(self._im_proc.process)
		self._network = NetworkManager(self._vid_decoder,self,network_config)
		self._controller_manager = Controller.ControllerManager(self)	

		# Start video and navdata stream on drone
		self._control.start_navdata()
		self._control.start_video()
				
		# Reset drone
		self._control.reset()
	
		# Configure drone camera - again! Just to make sure it happens.
		self._control.view_camera(1) # channel 1 = downward facing camera
		
		# State setup
		self._state = State.CommunicationState(self,drone_id)
		self.state_id = 0
	
		# Keep drone_id
		self.raw_status['drone_id'] = drone_id

	def request_state(self,state_id):
		"""
		Decide what to do based on a requested state_id
			Either  maintain current state
			Or 	request transition towards requested state
		"""

		if state_id == self.state_id:
			self._state.maintain()
		else:
			self._state.transition(state_id)

	def check_exit(self):
		self._state.check_exit()
	
	def change_state(self,state):
		self._state = state[0]
		self.state_id = state[1]

	def reset(self):
		self._control.reset()

	def flat_trim(self):
		self._control.flat_trim()
		
	def take_off(self):
		self._control.take_off()

	def land(self):
		self._control.land()
		
	def set_altitude(self,r):
		self._height_control = self._controller_manager.create_proportional_controller(self,'altitude','gas','gas_stable',0.02,r,0.2)

	def hold_marker(self,marker_id):
		# Set flag
		self.holding_marker = True

		# Change marker being tracked and update info
		if not self.raw_status['marker_id'] == marker_id:
			self.raw_status['marker_id'] = marker_id
			self.raw_status['marker_position_x'] = self.visible_marker_info[str(marker_id)][0]
			self.raw_status['marker_posistion_y'] = self.visible_marker_info[str(marker_id)][1]
		
		# Stop the drone hovering by itself (this is only sent to the drone with another command but that's OK)
		self.drone_input['hover'] = False
		
		# Initiate roll and pitch controllers
		self._marker_control_roll = self._controller_manager.create_lead_lag_2_controller(self,'marker_distance_x','roll','roll_stable',0.001,0.15,0.025,0.04,0,0.5)
		self._marker_control_pitch = self._controller_manager.create_lead_lag_2_controller(self,'marker_distance_y','pitch','pitch_stable',0.001,0.15,0.025,0.04,0,0.5)
	
	def get_visible_markers(self):
		"""
		Returns a list of currently visible marker ids
		"""
		return self.visible_marker_info.keys()

	def update_route(self,route):
		self.route = route

	def update_position(self,marker_data):
		# Update object's record of marker positions
		self.visible_marker_info = marker_data

		# Update record for the marker currently being tracked if there is no new information then keep old information
		if str(self.raw_status['marker_id']) in marker_data:
			self.raw_status['marker_distance_x'] = -1 * marker_data[str(self.raw_status['marker_id'])][0]
			self.raw_status['marker_distance_y'] = -1 * marker_data[str(self.raw_status['marker_id'])][1]
		
		# Print to console
		#print(self.marker_distance)

	def update(self,status):
		"""
		Merge status with local version and send to the status updater with appropriate drone_id label.
		"""
		status['drone_id'] = self.drone_id
		self.update_raw(status)
		self._updater.update(self.raw_status)

	def update_raw(self,status):
		self.raw_status = dict(self.raw_status.items() + status.items())

	def update_drone(self,status):
		self.drone_status = status

class NetworkManager(object):
	"""
	A class which manages the sending and receiving of packets over the network.
	It stores the relevant data of received packets and sends packets when requested.
	
	IP address of drone: config.['host']
	Localhost: 127.0.0.1
	"""

	def __init__(self,_vid_decoder,_update,network_config):
		"""
		Initialise the class
		"""
		
		# Variables
		self.seq = 0
		self.ready_video = False
		self.ready_control = False
		
		# Variable assignment
		self.config = network_config
		
		# Pointer assignment
		self._vid_decoder = _vid_decoder
		self._update = _update
		
		# Variable assignment
		self.config = network_config
		
		# Set up a UDP listening socket on port for control data
		self.socket_control = QtNetwork.QUdpSocket()
		if not self.socket_control.bind(QtNetwork.QHostAddress.Any, self.config['control_data_port']):
			raise RuntimeError('Error binding to port: %s' % (self.socket_control.errorString()))
		self.socket_control.readyRead.connect(self.readControlData)
    
		# Set up a UDP listening socket on port for video data
		self.socket_video = QtNetwork.QUdpSocket()
		if not self.socket_video.bind(QtNetwork.QHostAddress.Any, self.config['video_data_port']):
			raise RuntimeError('Error binding to port: %s' % (self.socket_video.errorString()))
		self.socket_video.readyRead.connect(self.readVideoData)

		# 
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def sendControl(self,data):
		# Send state to the drone
		self.seq += 1
		#print('state is', json.dumps({'seq': self.seq, 'state': data}))
		self.sock.sendto(json.dumps({'seq': self.seq, 'state': data}), (self.config['bind_host'], self.config['control_port'])) 
	
	def readControlData(self):
		"""
		Called when there is some interesting data to read on the control socket
		"""
		while self.socket_control.hasPendingDatagrams():
			sz = self.socket_control.pendingDatagramSize()
			(data, host, port) = self.socket_control.readDatagram(sz)
	
			# Some hack to account for PySide vs. PyQt differences
			if qt.USES_PYSIDE:
				data = data.data()

	        # Parse the packet
			self.packet = json.loads(data.decode())
			# Keep packet if it contains status information
			if self.packet['type'] == 'demo':
				self.packet['type'] = 'raw' #Change type to conform to status format of application
				self._update.update(self.packet)

				# Update status of the Control Network when ready
				if self.ready_control == False:
					#print("Control Ready")
					self.ready_control = True
					self._update.control_network_activity_flag = True
				
			#Print it prettily
			#print(json.dumps(self.packet, indent=True))

	def readVideoData(self):
		"""Called when there is some interesting data to read on the video socket."""
		while self.socket_video.hasPendingDatagrams():
			sz = self.socket_video.pendingDatagramSize()
			(data, host, port) = self.socket_video.readDatagram(sz)

			# Some hack to account for PySide vs. PyQt differences
			if qt.USES_PYSIDE:
					data = data.data()
		
			# Decode video data and pass result to the ImageProcessor instance
			self._vid_decoder.decode(data)
			
			if self.ready_video == False:
				#print("Video Ready")
				self.ready_video = True
				self._update.video_network_activity_flag = True
