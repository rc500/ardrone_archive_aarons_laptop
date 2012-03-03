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
		ipl_image = cv.CreateImageHeader((320,240), cv.IPL_DEPTH_8U, 2)		# Downward camera size is actually 176x144
		cv.SetData(ipl_image, data)
		# Convert image to RGB888 which is more OpenCV friendly
		CV_image = cv.CreateImage((320,240), cv.IPL_DEPTH_8U, 3)
		cv.CvtColor(ipl_image, CV_image, cv.CV_BGR5652BGR)

		# --- ARUCO FORMAT ---
		PIL_image = self.cv2array(CV_image)
		
		# Find midpoint of image
		CV_image_size = cv.GetSize(CV_image)
		#CV_image_midpoint = (CV_image_size[0]/2,CV_image_size[1]/2)
		CV_image_midpoint = (176/2,144/2) # need to use this for downward facing camera as image does not take up whole 320x240 but is decoded as such
		
		# Detect and draw on marker centerpoints
		marker_dict = {}
		for m in detect_markers(PIL_image):
			marker_center = (m.centroid_x(), m.centroid_y())
			cv.Line(CV_image,CV_image_midpoint,marker_center,cv.Scalar(200,200,200))		
			# Update relative position
			relative_position = (marker_center[0] - CV_image_midpoint[0], marker_center[1] - CV_image_midpoint[1])
			marker_dict[str(m.id())]=relative_position

		# Update PositionalControl with info from processed image
		self._update.update_position(marker_dict)
		# Show processed image
		self._im_viewer.show(CV_image)
		
	def cv2array(self,im):
		depth2dtype = {
        cv.IPL_DEPTH_8U: 'uint8',
        cv.IPL_DEPTH_8S: 'int8',
        cv.IPL_DEPTH_16U: 'uint16',
        cv.IPL_DEPTH_16S: 'int16',
        cv.IPL_DEPTH_32S: 'int32',
        cv.IPL_DEPTH_32F: 'float32',
        cv.IPL_DEPTH_64F: 'float64',}

		arrdtype=im.depth
		a = np.fromstring(
		im.tostring(),
        dtype=depth2dtype[im.depth],
        count=im.width*im.height*im.nChannels)
         
		a.shape = (im.height,im.width,im.nChannels)
		return a

class ImageViewer(object):
	

	def __init__(self,drone_id):
		self.win_title = "Drone " + str(drone_id) + " Video Stream"
		cv.NamedWindow(self.win_title,cv.CV_WINDOW_AUTOSIZE)

	def show(self,frame):
		cv.ShowImage(self.win_title,frame)
