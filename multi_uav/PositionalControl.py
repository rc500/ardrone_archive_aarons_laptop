import os
import sys
import json, socket

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

	marker_distance = (0,0)
	
	def __init__(self,drone_id,_control):
		# --- ASSIGN POINTERS ---
		self._control=_control

		# --- INITIALISE APPLICATION OBJECTS ----
		self._im_proc = ImageProcessor.ImageProcessor(self,drone_id)
		self._vid_decoder = Videopacket.Decoder(self._im_proc.process)
				
		# Start video on drone
		self._control.start_video()

		# Set up a UDP listening socket on port 5561 for control data
		self.socket_control = QtNetwork.QUdpSocket()
		if not self.socket_control.bind(QtNetwork.QHostAddress.Any, 5561):
			raise RuntimeError('Error binding to port: %s' % (self.socket_control.errorString()))
		self.socket_control.readyRead.connect(self.readControlData)
    
		# Set up a UDP listening socket on port 5562 for video data
		self.socket_video = QtNetwork.QUdpSocket()
		if not self.socket_video.bind(QtNetwork.QHostAddress.Any, 5562):
			raise RuntimeError('Error binding to port: %s' % (self.socket_video.errorString()))
		self.socket_video.readyRead.connect(self.readVideoData)

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
	      #if packet['type'] == 'demo':
			#height = packet['altitude']
			#height_control(height)
	
	      ## Print it prettily
	      print(json.dumps(packet, indent=True))
	      		
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
		
	def update(self,distance):
		
		self.marker_distance = distance
		print(self.marker_distance)
