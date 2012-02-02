import os
import sys
import json, socket, time

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtNetwork = qt.import_module('QtNetwork')

from . import ImageProcessor
import ardrone.core.videopacket as Videopacket

class PositionalControl(object):
	"""
	The core drone control object which contains functions to control the position of an individual drone.
	This is done through the ControlLoop object.
	"""

	marker_distance = (0,0)
	state = {
	                'roll': 0.0,
	                'pitch': 0.0,
	                'yaw': 0.0,
	                'gas': 0.0,
	                'take_off': False,
	                'reset': False,
	                'hover': True,
	                                };
	
	def __init__(self,drone_id,_control,pseudo_network):
		# --- ASSIGN POINTERS ---
		self._control=_control
		self._pseudo_network = pseudo_network
		
		# --- INITIALISE APPLICATION OBJECTS ----
		self._im_proc = ImageProcessor.ImageProcessor(self,drone_id)
		self._vid_decoder = Videopacket.Decoder(self._im_proc.process)
		self._network = NetworkManager(self._vid_decoder,self._pseudo_network)
		
		# Start video and navdata stream on drone
		self._control.start_video()
		self._control.start_navdata()
				
		# Reset drone
		self._control.reset()

		# --- INITIALISE CONTROL OBJECTS ---
		self._height_control = ProportionalController(0.02)
		self._roll_control = ProportionalController(0.02)

	def take_off(self):
		self._control.flat_trim()
		time.sleep(3.0)
		self._control.take_off()
		time.sleep(4.0)

	def land(self):
		self._control.land()
		
	def set_altitude(self,r):
		self.state['altitude'] = self._height_control.get_control(self.packet['altitude'],r)
		_network.sendControl(self.state)		

	def update(self,distance):
		self.marker_distance = distance
		print(self.marker_distance)
		
class NetworkManager(object):
	"""
	A class which manages the sending and receiving of packets over the network.
	It stores the relevant data of received packets and sends packets when requested.
	"""
	ready_control = False
	ready_video = False
	
	HOST, HOST2, PORT_SEND, PORT_CONTROL, PORT_VIDEO, PORT_STATUS = ('127.0.0.1', '192.168.1.1', 5560, 5561, 5562, 5557)
	seq = 0

	def __init__(self,_vid_decoder,_pseudo_network):
		"""
		Initialise the class
		"""
		# Pointer assignment
		self._vid_decoder = _vid_decoder
		self._pseudo_network = _pseudo_network
		
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
		#print('state is', json.dumps({'seq': self.seq, 'state': self.state}))
		self.sock.sendto(json.dumps({'seq': self.seq, 'state': data}), (self.HOST, self.PORT_SEND)) 
	
	def sendStatus(self,status):
		# Send status over the network
		#self.sock.sendto(status, (self.HOST2, self.PORT_STATUS))
		self._pseudo_network.update_status(status)
		print("Status sent")

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
	        
			#Run height control if packet contains height information
#			if self.packet['type'] == 'demo':
				# Parse the packet
			self.packet = json.loads(data.decode())
			
			if self.ready_control == False:
				print("Control Ready")
				self.sendStatus('ControlReady')
				self.ready_control = True
				
			## Print it prettily
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
				print("Video Ready")
				self.sendStatus('VideoReady')
				self.ready_video = True
				

class ProportionalController(object):
	"""
	Implementation of a proportional controller which takes a position and returns a correcting velocity
	
	CONTROLLER:
	G(s) = K
	
	The controller output magnitude is hard limited to 1
	"""
		
	correction_step = 0.1

	def __init__(self,k=0.02):
		self.k = k
		
	def get_control(self,y,r):
		#implement proportional control
		error = r-y
		#print('Current error is', error)
		psuedo_error = error * self.k
		correction = self.correction_step * psuedo_error
		if correction >= 1:
			correction = 1
		elif correction <= -1:
			correction = -1
		print ("correction = " + str(correction))
		return correction
		
class LeadLagController(object):

	"""
	Implementation of a lead-lag controller which takes a position and returns a correcting velocity
	
	ANALOGUE CONTROLLER:
	G(s) = (s + a) / (s + b)
	
	DIGITAL CONTORLLER:
			z(2 + aT) + (1 - aT)
	G(z) =  --------------------
			z(2 + bT) + (1 - bT)
	
	DIFFERENCE EQUATION:
						x[k-1]	 y[k-1]	   y[k]
	x[k] =    (1-bT){ -	------ + ------ + ------ }
						2 + bT	 2 + aT	  1 - aT
	"""
               
	def __init__(self,a,b,T):
		self.a = a
		self.b = b
		self.T = T
		self.x = 0		# x[k-1]
		self.y = (0,0)	# y[k-1],y[k]

	def get_control(self,y):
		# Update latest output
		self.y[1] = y
		
		# Calculate x[k]
		part_1 = -1 * (1-(self.b*self.T))
		part_2a = self.x / (2 + (self.b * self.T))
		part_2b = self.y[0] / (2 + (self.a * self.T))
		part_2c = self.y[1] / (1 - (self.a * self.T))
		self.x = part_1 * (part_2a + part_2b + part_2c)
		
		# Update y
		self.y[0] = self.y[1]
		
		# Return x
		return self.x
