# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import objects to initialise
from ardrone.core.controlloop import ControlLoop
from ardrone.platform import qt as platform

class Application(object):
	
	def __init__(self):
		
		# ---- APPLICATION SETUP ----
		# Create a QtCoreApplication loop (NB remember to use QApplication instead if wanting GUI features)
		self.app = QtCore.QCoreApplication(sys.argv)

		# Wire up Ctrl-C to call QApplication.quit()
		signal.signal(signal.SIGINT, lambda *args: self.app.quit())

		# ---- DRONES SETUP ----
		# Initialialise a control loop and attempt to open connection to first drone
		connection = platform.Connection()
		self._drone1 = ControlLoop(connection)
		
		# --- INITIALISE APPLICATION OBJECTS ----
		self._positionalControl=
