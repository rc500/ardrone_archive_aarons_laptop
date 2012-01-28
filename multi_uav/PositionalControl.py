import os
import sys

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from . import ImageProcessor

class PositionalControl(object):

	def __init__(self,drone_id,_control):
		# --- ASSIGN POINTERS ---
		self._control=_control

		# --- INITIALISE APPLICATION OBJECTS ----
		self._im_proc = ImageProcessor.ImageProcessor(drone_id)
		
		# Start video on drone
		self._control.start_video()

