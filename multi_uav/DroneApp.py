import os
import signal
import sys
import time

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import objects to initialise
from ardrone.core.controlloop import ControlLoop
from ardrone.platform import qt as platform
from . import network_config as config
from . import AppController

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')
		
class DroneApp(object):

	def __init__(self):
		# ---- SYSTEM CONFIGURATION ----
		drones = (1,)
		configs = (config.drone1,)

		# Wire up Ctrl-C to safely land drones and end the application
		signal.signal(signal.SIGINT, lambda *args: self.finish())

		# ---- APPLICATION SETUP ----
		# Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
		self.app = QtCore.QCoreApplication(sys.argv)
		self.app_controller = AppController.AppController(drones,configs)

		print("DroneApp finished initialising - DroneApp")

	def run(self):
		print("Run called - DroneApp")
		#self.app.exec_()
		print("App.exec_() run successfully - DroneApp")
		self.app_controller.start()
	
	def finish(self):
		# NB - Currently Drones are landed in an unconfirmed way (i.e. commands are sent and being on the ground is not confirmed - this should be done via states)
		self._pos_control_1.land()
		self._pos_control_2.land()
		self.app.quit()
