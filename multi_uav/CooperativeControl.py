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

	phase = 0
	
	def __init__(self,_drone1): # Will want to add in _drone2 in time
		# --- INITIALISE APPLICATION OBJECTS ----
		#self._status_viewer = # add at some point
		self._network = NetworkManager(self)
		
		self._drone1 = _drone1
		
	def start(self):
		print("Program started")
		
		# Phase 1 - take off to a height
		self.phase = 1
		self._drone1.take_off()
		self._drone1.set_altitude(1000)

	def next_phase(self):
		"""
		Moves onto next phase
		"""
		self.phase = self.phase + 1
		if self.phase == 2:
			# Phase 2 - correct to marker
			self.correct_to_marker()
			
	def correct_to_marker(self):
		print("-----------------------------------------------Marker correction started--------------------------------------------------")
		# Insert marker correction code here - requires use of downward facing camera first
		pass
		
class NetworkManager(object):
	"""
	A class which manages the sending and receiving of packets over the network.
	It stores the relevant data of received packets and sends packets when requested.
	
	IP address of drone: 192.168.1.1
	Localhost: 127.0.0.1
	"""
	
	ready = 2
	
	PORT_STATUS = 5563

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

	def readStatusData(self):
		"""
		Called when there is some interesting data to read on the status socket.
		Calls the next phase functions when desired status is achieved.
		"""
		while self.socket_status.hasPendingDatagrams():
			sz = self.socket_status.pendingDatagramSize()
			(data, host, port) = self.socket_status.readDatagram(sz)
	
			## --- INITIALISING STATUS CHECKS --- ##
			if data == 'ControlReady':
				self.ready = self.ready - 1
				print("Coop caught Control Ready; awaiting %r more processes to initialise" % self.ready)
			
			if data == 'VideoReady':
				self.ready = self.ready - 1
				print("Coop caught Video Ready; awaiting %r more processes to initialise" % self.ready)
			
			if self.ready == 0:
				self._coop.start()
				self.ready = 1 # to make sure this isn't called again

			## --- CONTROL STATUS CHECK --- ##
			if data == 'ControlAchieved':
				self._coop.next_phase()
				
