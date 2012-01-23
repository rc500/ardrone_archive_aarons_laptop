import os
import signal
import sys
import socket, time

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import QtCore module (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')

import cv
	
	
class ImageViewer(object):

	imTitle = ("lena.jpg", "faces_detected.jpg")
	counter = 0
	win_frame = "Drone Video Feed"

	def __init__(self):
		# Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
		self.app = QtCore.QCoreApplication(sys.argv)

		# Wire up Ctrl-C to call QApplication.quit()
		signal.signal(signal.SIGINT, lambda *args: self.app.quit())

		# Create a timer to call toggle() every second
		self.toggle_timer = QtCore.QTimer()
		self.toggle_timer.setInterval(1000)
		self.toggle_timer.timeout.connect(self.toggle)
		self.toggle_timer.start()	

		# Create a window in which to place frames
		cv.NamedWindow(self.win_frame, cv.CV_WINDOW_AUTOSIZE) #probably no need to autosize
		
	def run(self):
		self.app.exec_()
		
	def toggle(self):
		# Toggle image in window
		self.showImage(self.imTitle[self.counter])
		
		# Toggle 'counter' value
		if self.counter == 0:
			self.counter = 1
		else:
			self.counter = 0
		
	def showImage(self, title):
		cv.ShowImage(self.win_frame, cv.LoadImage(title,1))

if (__name__ == '__main__'):
  image_app = ImageViewer()
  image_app.run()
