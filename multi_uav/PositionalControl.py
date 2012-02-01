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

	HOST, PORT_SEND, PORT_CONTROL, PORT_VIDEO = ('127.0.0.1', 5560, 5561, 5562)
	seq = 0
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
	
	def __init__(self,drone_id,_control):
		# --- ASSIGN POINTERS ---
		self._control=_control

		# --- INITIALISE APPLICATION OBJECTS ----
		self._im_proc = ImageProcessor.ImageProcessor(self,drone_id)
		self._vid_decoder = Videopacket.Decoder(self._im_proc.process)

		# Start video and navdata stream on drone
		self._control.start_video()
		self._control.start_navdata()
				
		# Take off drone1
		self._control.reset()
		time.sleep(3.0)
		print("reset")
		self._control.flat_trim()
		time.sleep(3.0)
		print("trimmed")
		self._control.take_off()
		time.sleep(6.0)
		print("take off")
		
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
		
		# --- INITIALISE CONTROL OBJECTS ---
		self._height_control = ProportionalController(0.02)
		self._roll_control = ProportionalController(0.02)

		# Bit of stuff
		time.sleep(3.0)
		self._control.land()

	def readControlData(self):
	    """Called when there is some interesting data to read on the control socket."""
	
	    while self.socket_control.hasPendingDatagrams():
	      sz = self.socket_control.pendingDatagramSize()
	      (data, host, port) = self.socket_control.readDatagram(sz)
	
	      # Some hack to account for PySide vs. PyQt differences
	      if qt.USES_PYSIDE:
	        data = data.data()
	  
	      # Parse the packet
	      packet = json.loads(data.decode())
	
		  #Run height control if packet contains height information
	      if packet['type'] == 'demo':
			height = packet['altitude']
			self.state['altitude'] = self._height_control.get_control(y=height,r=1000)
			self.send_state()
			
	      ## Print it prettily
	      #print(json.dumps(packet, indent=True))
	      		
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
		
	def send_state(self):
			# Send state to the drone
			self.seq += 1
			#print('state is', json.dumps({'seq': self.seq, 'state': self.state}))
			self.sock.sendto(json.dumps({'seq': self.seq, 'state': self.state}), (self.HOST, self.PORT_SEND)) 
	        
	def update(self,distance):
		self.marker_distance = distance
		print(self.marker_distance)

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
