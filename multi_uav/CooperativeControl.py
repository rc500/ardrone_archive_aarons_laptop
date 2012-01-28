import os
import sys

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class CooperativeControl(object):
	def __init__(self,_drone1): # Will want to add in _drone2 in time
		# --- INITIALISE APPLICATION OBJECTS ----
		#self._status_viewer = 
		
		# --- SETUP TIMER ---
		

		pass

	def run(self):
		pass
