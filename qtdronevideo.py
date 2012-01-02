import os
import signal
import sys
import socket, time
import cv
#from PIL import Image

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')

# Import the actual drone control stuff.
from ardrone.core.controlloop import ControlLoop	
from ardrone.platform import qt as platform

# Import video decoder
import ardrone.core.videopacket as videopacket

class imageViewer(object):

	win_title = "Drone Video Feed"

	def __init__(self):
		# Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
		self.app = QtCore.QCoreApplication(sys.argv)

		# Wire up Ctrl-C to call QApplication.quit()
		signal.signal(signal.SIGINT, lambda *args: self.app.quit())

		# Initialise the drone control loop and attempt to open a connection.
		connection = platform.Connection()
		self._control = ControlLoop(connection, video_cb=None, navdata_cb=None)

		# Create a window in which to place frames
		cv.NamedWindow(self.win_title, cv.CV_WINDOW_AUTOSIZE) #probably no need to autosize

		# Set up a UDP listening socket on port 5562 which calls readData upon socket activity
		self.socket = QtNetwork.QUdpSocket()
		if not self.socket.bind(QtNetwork.QHostAddress.Any, 5562):
			raise RuntimeError('Error binding to port: %s' % (self.socket.errorString()))
		self.socket.readyRead.connect(self.readData)

		# Start video on drone
		self._control.start_video()
		
	def run(self):
		self.app.exec_()
		
	def readData(self):
		"""Called when there is some interesting data to read on the video socket."""
		while self.socket.hasPendingDatagrams():
			sz = self.socket.pendingDatagramSize()
			(data, host, port) = self.socket.readDatagram(sz)

		# Some hack to account for PySide vs. PyQt differences
		if qt.USES_PYSIDE:
			data = data.data()
		
		# Decode video data and pass result to showImage
		videopacket.Decoder(self.showImage).decode(data)
			
	def showImage(self, data):
		"""
		Displays argument image in window using openCV.
		data argument must be a string containing a 16 bit unsigned RGB image (RGB16 == RGB565).
		"""
		
		iplimage = cv.CreateImageHeader((320,240), cv.IPL_DEPTH_16U, 1)
		cv.SetData(iplimage, data)
		cv.ShowImage(self.win_title, iplimage)
				
if (__name__ == '__main__'):
  image_app = imageViewer()
  image_app.run()
