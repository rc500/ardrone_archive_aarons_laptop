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
		self.drones = (1,)
		self.configs = (config.drone1,)

		# Wire up Ctrl-C to safely land drones and end the application
		signal.signal(signal.SIGINT, lambda *args: self.finish())

		# ---- APPLICATION SETUP ----
		# Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
		self.app = QtCore.QCoreApplication(sys.argv)
		self.app_controller = AppController.AppController(self.drones,self.configs)

	def run(self):
		self.app_controller.start()
		self.app.exec_()
	
	def finish(self):
		self.app_controller.finish()
		self.app.quit()
