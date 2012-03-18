import os
import signal
import sys

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import objects to initialise
from ardrone.core.controlloop import ControlLoop
from ardrone.platform import qt as platform
from . import PositionalControl
from . import CooperativeControl
from . import network_config as config

import time
# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')
		
class DroneApp(object):

	def __init__(self):
		# ---- APPLICATION SETUP ----
		# Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
		self.app = QtCore.QCoreApplication(sys.argv)

		# ---- DRONES SETUP ----
		# Initialialise a control loop and attempt to open connection to first drone
		connection1 = platform.Connection()
		connection2 = platform.Connection()
		self._drone1 = ControlLoop(connection1, **config.drone1)
		self._drone2 = ControlLoop(connection2, **config.drone2)
		
		# --- INITIALISE APPLICATION OBJECTS ----
		self._pos_control_1 = PositionalControl.PositionalControl(1,self._drone1,self,config.drone1)
		self._pos_control_2 = PositionalControl.PositionalControl(2,self._drone2,self,config.drone2)
		self._coop_control = CooperativeControl.CooperativeControl((1,2),(self._pos_control_1,self._pos_control_2))

		# Wire up Ctrl-C to safely land drones and end the application
		signal.signal(signal.SIGINT, lambda *args: self.finish())

	def run(self):
		self.app.exec_()
	
	def finish(self):
		# NB - Currently Drones are landed in an unconfirmed way (i.e. commands are sent and being on the ground is not confirmed - this should be done via states)
		self._pos_control_1.land()
		self._pos_control_2.land()
		self.app.quit()

	def send_status(self,status):
		self._coop_control._network.readStatusData_pseudo(status)
