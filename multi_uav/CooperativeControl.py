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

class CooperativeControl(object):
	
	ready = 2
	
	def __init__(self,_drone1): # Will want to add in _drone2 in time
		# --- INITIALISE APPLICATION OBJECTS ----
		#self._status_viewer = # add at some point
		#self._network = NetworkManager(self) # Why doesn't this work?
		
		self._drone1 = _drone1
	
	def update_status(self,data):
		if data == 'ControlReady':
			print("Coop caught Control Ready; ready is at %r" % (self.ready,))
			self.ready = self.ready - 1
		
		if data == 'VideoReady':
			self.ready = self.ready - 1
			
		if self.ready == 0:
			self.main()
		
	def main(self):
		print("here")
		self._drone1.take_off()
		time.sleep(3.0)
		self._drone1.land()
		sys.exit()


class NetworkManager(object):
	#Currently not working ...
	"""
	A class which manages the sending and receiving of packets over the network.
	It stores the relevant data of received packets and sends packets when requested.
	"""
	
	ready = 2
	
	HOST, PORT_STATUS = ('192.168.1.1', 5557)

	def __init__(self,initialiser):
		"""
		Initialise the class
		"""
		self._coop = initialiser
		
		# Set up a UDP listening socket on port for status data
		self.socket_status = QtNetwork.QUdpSocket()
		if not self.socket_status.bind(QtNetwork.QHostAddress.Any, self.PORT_STATUS):
			raise RuntimeError('Error binding to port: %s' % (self.socket_status.errorString()))
		self.socket_status.readyRead.connect(self.readStatusData)

		# 
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def readStatusData(self):
		"""
		Called when there is some interesting data to read on the status socket
		"""
		
		print("Status packet caught")
		while self.socket_status.hasPendingDatagrams():
			sz = self.socket_status.pendingDatagramSize()
			(data, host, port) = self.socket_status.readDatagram(sz)
	
			if data == 'ControlReady':
				print("Coop caught Control Ready; ready is at %r", self.ready)
				self.ready = self.ready - 1
			
			if data == 'VideoReady':
				
				self.ready = self.ready - 1
			
			if self.ready == 0:
				_coop.main()
