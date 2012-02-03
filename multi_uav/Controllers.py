import os
import sys
import json, socket

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import qt modules (platform independant)
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')

class Controller(object):
	"""
	Class forming the base functionality of a controller
	"""
		
	correction_step = 0.1

	def __init__(self,_control,feedback_type,output_type):
		# Assign pointers
		self._control = _control

		# Assign types
		self.feedback_type = feedback_type
		self.output_type = output_type

		# Create a little 'heartbeat' timer that will call heartbeat() every so often.
		self.heartbeat_timer = QtCore.QTimer()
		self.heartbeat_timer.setInterval(20) # ms
		self.heartbeat_timer.timeout.connect(self.heartbeat)

	def start_control(self,r):
		# Assign control reference
		self.r = r
		
		# Start control
		self.heartbeat_timer.start()
	
	def stop_control(self):
		# Stop control
		self.heartbeat_timer.stop()

	def y(self):
		# Fetch feedback value
		y = self._control.packet[self.feedback_type]
		return y

	def heartbeat(self):
		# --- calculations would be here ---#

		# Don't forget to add
		# self.output(output)
		# at the end
		pass
		
	def output(self,output):
		# Print the output
		print ("correction = " + str(output))
		
		# Send the update to the drone, via the structure in PositionalControl (so it has a copy)
		self._control.state[self.output_type] = output
		self._control._network.sendControl(self._control.state)
		
class ProportionalController(Controller):
	"""
	Implementation of a proportional controller which takes a position and returns a correcting velocity
	
	CONTROLLER:
	G(s) = K
	
	The controller output magnitude is hard limited to 1
	"""
		
	def __init__(self,_control,feedback_type,output_type,k):
		# Set up controller parameters
		self.k = k

		# Initialise as Controller base class
		Controller.__init__(self, _control,feedback_type,output_type)
		
	def heartbeat(self):
		# Calculate output value
		error = self.r-self.y()
		psuedo_error = error * self.k
		correction = self.correction_step * psuedo_error
		if correction >= 1:
			correction = 1
		elif correction <= -1:
			correction = -1
			
		# Continue as per Controller base class
		self.output(correction)
		
class LeadLagController(object):
# Not yet implemented with Controller base class yet
	"""
	Implementation of a lead-lag controller which takes a position and returns a correcting velocity
	
	ANALOGUE CONTROLLER:
	G(s) = (s + a) / (s + b)
	
	DIGITAL CONTORLLER:
			z(2 + aT) + (1 - aT)
	G(z) =  --------------------
			z(2 + bT) + (1 - bT)
	
	DIFFERENCE EQUATION:
						x[k-1]	 y[k-1]	   y[k]
	x[k] =    (1-bT){ -	------ + ------ + ------ }
						2 + bT	 2 + aT	  1 - aT
	"""
               
	def __init__(self,a,b,T):
		self.a = a
		self.b = b
		self.T = T
		self.x = 0		# x[k-1]
		self.y = (0,0)	# y[k-1],y[k]

	def get_control(self,y):
		# Update latest output
		self.y[1] = y
		
		# Calculate x[k]
		part_1 = -1 * (1-(self.b*self.T))
		part_2a = self.x / (2 + (self.b * self.T))
		part_2b = self.y[0] / (2 + (self.a * self.T))
		part_2c = self.y[1] / (1 - (self.a * self.T))
		self.x = part_1 * (part_2a + part_2b + part_2c)
		
		# Update y
		self.y[0] = self.y[1]
		
		# Return x
		return self.x
