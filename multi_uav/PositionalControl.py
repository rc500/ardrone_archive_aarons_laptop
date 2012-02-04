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
from . import ImageProcessor
import ardrone.core.videopacket as Videopacket

class PositionalControl(object):
	"""
	The core drone control object which contains functions to control the position of an individual drone.
	This is done through the ControlLoop object.
	"""
	
	marker_distance = (0,0)

	commanded_state = {
	                'roll': 0.0,
	                'pitch': 0.0,
	                'yaw': 0.0,
	                'gas': 0.0,
	                'take_off': False,
	                'reset': False,
	                'hover': True,
	                                };
	
	current_state = {
					"type": "initialise",
					'marker_distance_x': 0.0,
					'marker_distance_y': 0.0,
									};
	
	def __init__(self,drone_id,_control,pseudo_network):
		# --- ASSIGN POINTERS ---
		self._control=_control
		self._pseudo_network = pseudo_network
		
		# --- INITIALISE APPLICATION OBJECTS ----
		self._im_proc = ImageProcessor.ImageProcessor(self,drone_id)
		self._vid_decoder = Videopacket.Decoder(self._im_proc.process)
		self._network = NetworkManager(self._vid_decoder,self._pseudo_network,self)
		
		# Configure drone camera
		self._control.view_camera(1) # channel 1 = downward facing camera
		
		# Start video and navdata stream on drone
		self._control.start_navdata()
		self._control.start_video()
				
		# Reset drone
		self._control.reset()
		self._control.reset()
		self._control.reset()
		
	def take_off(self):
		self._control.flat_trim()
		self._control.take_off()

	def land(self):
		self._control.land()
		
	def set_altitude(self,r):
		self._height_control = Controller.ProportionalController(self,'altitude','gas',0.02)
		self._height_control.start_control(r)

	def hold_marker(self):
		# Stop the drone hovering by itself
		self.commanded_state['hover'] = False
		
		# Initiate roll and pitch controllers
		self._marker_control_roll = Controller.LeadLagController(self,'marker_distance_x','roll',0.2,0.15,0.05,0.02)
		self._marker_control_pitch = Controller.LeadLagController(self,'marker_distance_y','pitch',0.2,0.15,0.05,0.02)
		
		# Start control
		self._marker_control_roll.start_control(0)
		self._marker_control_pitch.start_control(0)
		
	
	def update(self,distance):
		# Keep a separate record of distance from marker
		self.marker_distance = distance
		
		# Update object's record of drone state
		self.current_state['marker_distance_x'] = -1 * distance[0]
		self.current_state['marker_distance_y'] = -1 * distance[1]
		
		# Print to console
		#print(self.marker_distance)
	
	def update_packet(self,packet):
		# Update object's record of drone state with new information
		self.current_state = packet
		
		# Copy back in marker distance information
		self.update(self.marker_distance)
			
class NetworkManager(object):
	"""
	A class which manages the sending and receiving of packets over the network.
	It stores the relevant data of received packets and sends packets when requested.
	
	IP address of drone: 192.168.1.1
	Localhost: 127.0.0.1
	"""
	ready_control = False
	ready_video = False
	
	HOST, PORT_SEND, PORT_CONTROL, PORT_VIDEO, PORT_STATUS = ('127.0.0.1', 5560, 5561, 5562, 5563)
	seq = 0

	def __init__(self,_vid_decoder,_pseudo_network,_update):
		"""
		Initialise the class
		"""
		# Pointer assignment
		self._vid_decoder = _vid_decoder
		self._pseudo_network = _pseudo_network
		self._update = _update
		
		# Set up a UDP listening socket on port for control data
		self.socket_control = QtNetwork.QUdpSocket()
		if not self.socket_control.bind(QtNetwork.QHostAddress.Any, self.PORT_CONTROL):
			raise RuntimeError('Error binding to port: %s' % (self.socket_control.errorString()))
		self.socket_control.readyRead.connect(self.readControlData)
    
		# Set up a UDP listening socket on port for video data
		self.socket_video = QtNetwork.QUdpSocket()
		if not self.socket_video.bind(QtNetwork.QHostAddress.Any, self.PORT_VIDEO):
			raise RuntimeError('Error binding to port: %s' % (self.socket_video.errorString()))
		self.socket_video.readyRead.connect(self.readVideoData)

		# 
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def sendControl(self,data):
		# Send state to the drone
		self.seq += 1
		#print('state is', json.dumps({'seq': self.seq, 'state': data}))
		self.sock.sendto(json.dumps({'seq': self.seq, 'state': data}), (self.HOST, self.PORT_SEND)) 
	
	def sendStatus(self,status):
		# Send status over the network
		self.sock.sendto(status, (self.HOST, self.PORT_STATUS))
		print("Status sent: %s" % status)		
		#self._pseudo_network.update_status(status)

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
				self._update.update_packet(self.packet)
				#Print it prettily
				#print(json.dumps(self.packet, indent=True))

			# Update status of the Control Network when ready
			if self.ready_control == False:
				print("Control Ready")
				self.sendStatus('ControlReady')
				self.ready_control = True
				
	      		
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
				print("Video Ready")
				self.sendStatus('VideoReady')
				self.ready_video = True
