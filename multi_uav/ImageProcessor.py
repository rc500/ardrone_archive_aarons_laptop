import os
import sys
import cv
from PIL import Image

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtNetwork = qt.import_module('QtNetwork')

import ardrone.core.videopacket as Videopacket
from ardrone.aruco import detect_markers

class ImageProcessor(object):
	def __init__(self,drone_id):

		# Set up a UDP listening socket on port 5562 which calls readData upon socket activity
		self.socket = QtNetwork.QUdpSocket()
		if not self.socket.bind(QtNetwork.QHostAddress.Any, 5562):
			raise RuntimeError('Error binding to port: %s' % (self.socket.errorString()))
		self.socket.readyRead.connect(self.readData)
	
		# --- INITIALISE APPLICATION OBJECTS ----
		self._im_viewer = ImageViewer(drone_id)
		self._vid_decoder = Videopacket.Decoder(self.process)
		
	def readData(self):
		"""Called when there is some interesting data to read on the video socket."""
		while self.socket.hasPendingDatagrams():
			sz = self.socket.pendingDatagramSize()
			(data, host, port) = self.socket.readDatagram(sz)

		# Some hack to account for PySide vs. PyQt differences
		if qt.USES_PYSIDE:
			data = data.data()
		
		# Decode video data and pass result to the ImageProcessor instance
		self._vid_decoder.decode(data)

	def process(self,data):

		# Create OpenCV header and read in drone video data as RGB565
		ipl_image = cv.CreateImageHeader((320,240), cv.IPL_DEPTH_8U, 2)		
		cv.SetData(ipl_image, data)
		
		# Convert image to RGB888 which is more OpenCV friendly
		CV_image = cv.CreateImage((320,240), cv.IPL_DEPTH_8U, 3)
		cv.CvtColor(ipl_image, CV_image, cv.CV_BGR5652BGR)
				
		# Convert prep - MAKE THIS BETTER
		cv.SaveImage("frame.png", CV_image)
		RGB_image = Image.open("frame.png").convert('RGB')
  
		# Convert image into aruco-friendly format (array)
		# arr = array(RGB_image) #will need this if wanting to draw onto image using aruco library
				
		# Find midpoint of image
		CV_image_size = cv.GetSize(CV_image)
		CV_image_midpoint = (CV_image_size[0]/2,CV_image_size[1]/2)

		# Detect and draw on marker centerpoints
		for m in detect_markers(RGB_image):
			coord = (m.centroid_x(), m.centroid_y())
			cv.Line(CV_image,CV_image_midpoint,coord,cv.Scalar(200,200,200))		

		# Convert back to OpenCV-friendly format (RGB888)
		#stringImage = Image.fromarray(arr).tostring()
		#cvImage = cv.CreateImageHeader((320,240), cv.IPL_DEPTH_8U, 3)
		#cv.SetData(cvImage, stringImage)
		
		# Show processed image
		self._im_viewer.show(CV_image)


class ImageViewer(object):
	

	def __init__(self,drone_id):
		self.win_title = "Drone " + str(drone_id) + " Video Stream"
		cv.NamedWindow(self.win_title,cv.CV_WINDOW_AUTOSIZE)

	def show(self,frame):
		cv.ShowImage(self.win_title,frame)