import os
import sys
import cv
import numpy as np
from PIL import Image
import StringIO

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ardrone.aruco import detect_markers

class ImageProcessor(object):
	def __init__(self,_update,drone_id):
	
		# --- INITIALISE APPLICATION OBJECTS ----
		self._update = _update
		self._im_viewer = ImageViewer(drone_id)

	def process(self,data):

		# --- OPEN_CV FORMAT ---
		# Create OpenCV header and read in drone video data as RGB565
		ipl_image = cv.CreateImageHeader((320,240), cv.IPL_DEPTH_8U, 2)		
		cv.SetData(ipl_image, data)
		# Convert image to RGB888 which is more OpenCV friendly
		CV_image = cv.CreateImage((320,240), cv.IPL_DEPTH_8U, 3)
		cv.CvtColor(ipl_image, CV_image, cv.CV_BGR5652BGR)

		# --- ARUCO FORMAT ---
		# Convert from rgb565 to rgb888 using PIL
		#arr = np.fromstring(data,dtype=np.uint16).astype(np.uint32)
		#arr = 0xFF000000 + ((arr & 0xF800) >> 8) + ((arr & 0x07E0) << 5) + ((arr & 0x001F) << 19)
		#PIL_image=Image.fromstring('RGB', (320,240), arr, 'raw', 'RGB', 0, 1)
		# Convert to RGB for aruco
		#aruco_image = PIL_image.convert('RGB')
		
		#buff = StringIO.StringIO()
		#buff.write(data)
		#buff.seek(0)
		#PIL_image = Image.open(buff)
		#aruco_image = PIL_image.convert('RGB')
		
		cv.SaveImage("frame.png",CV_image)
		PIL_image = Image.open("frame.png").convert('RGB')
		
		# Find midpoint of image
		CV_image_size = cv.GetSize(CV_image)
		CV_image_midpoint = (CV_image_size[0]/2,CV_image_size[1]/2)

		# Detect and draw on marker centerpoints - currently only works for one at a time
		for m in detect_markers(PIL_image):
			marker_center = (m.centroid_x(), m.centroid_y())
			cv.Line(CV_image,CV_image_midpoint,marker_center,cv.Scalar(200,200,200))		
			print("here")
			# Update relative position
			relative_position = (marker_center[0] - CV_image_midpoint[0], marker_center[1] - CV_image_midpoint[1])
			self._update.update(relative_position)
			print (relative_position)
			
		# Show processed image
		self._im_viewer.show(CV_image)

class ImageViewer(object):
	

	def __init__(self,drone_id):
		self.win_title = "Drone " + str(drone_id) + " Video Stream"
		cv.NamedWindow(self.win_title,cv.CV_WINDOW_AUTOSIZE)

	def show(self,frame):
		cv.ShowImage(self.win_title,frame)
