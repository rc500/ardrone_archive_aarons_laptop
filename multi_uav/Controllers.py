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
		
	def __init__(self,_control,feedback_type,output_type,update_key,error_margin,hard_limit=1):
		# Variables
		self.error_count = 0
		self.correction_step = 0.1
		self.error_margin = error_margin
		self.controller_status = {'type': 'raw'};

		# Assign pointers
		self._control = _control

		# Assign types
		self.feedback_type = feedback_type
		self.output_type = output_type
		self.hard_limit = hard_limit
		self.update_key = update_key
		
		# Create a little 'heartbeat' timer that will call heartbeat() every so often.
		self.heartbeat_timer = QtCore.QTimer()
		self.heartbeat_timer.setInterval(40) # ms
		self.heartbeat_timer.timeout.connect(self.heartbeat)

		# Debug initialisation
		#print ("%s control object initiated" % (self.feedback_type))
		
	def start_control(self,r):
		# Assign control reference
		self.r = r
		
		# Start control
		self.heartbeat_timer.start()
	
	def stop_control(self):
		# Stop control
		self.heartbeat_timer.stop()

		# Update status to reflect lack of control
		self.set_stability(False)
	
	def y(self):
		# Fetch feedback value
		y = self._control.current_state[self.feedback_type]
		return y

	def heartbeat(self):
		# --- calculations would be here ---#

		# Don't forget to add
		# self.check_error(error)
		# self.output(output)
		# at the end
		pass
		
	def check_error(self,error):
		"""
		Checks whether the error is within acceptable limits.
		If it is within limits then the controller has achieved its goal and posts this status to the network.
		"""
		#print ("check_error: %s against error_margin: %s" % (error,self.error_margin))
		# Check whether error is within limits
		if error <= self.error_margin and error >= -1*self.error_margin:
			self.error_count = self.error_count + 1
		else:
			self.error_count = 0
		
		# If error within limits for a suitable length of time then it has achieved its goal
		if self.error_count == 50:
			self.set_stability(True)

		elif self.error_count == 0:
			self.set_stability(False)			
		
	def set_stability(self,boolean):
		# Update flag denoting whether status has changed (this is so we can prevent overloading the StatusUpdater with unecessary updates)
		status_change_flag = not boolean and self.controller_status[self.update_key]

		# Update class status
		self.controller_status[self.update_key] = boolean

		# Update status
		if status_change_flag:
			self._status_updater.update(self.controller_status)
			
	def output(self,output):
		# Hard limit output
		if output >= self.hard_limit:
			output = self.hard_limit
		elif output <= -1 * self.hard_limit:
			output = -1 * self.hard_limit
			
		# Print the output
		#print ("%s correction = %s" % (self.output_type,output))
		
		# Send the update to the drone, via the structure in PositionalControl (so it has a copy)
		self._control.drone_input[self.output_type] = output
		#print (self._control.drone_input[self.output_type])
		self._control._network.sendControl(self._control.drone_input)

class ProportionalController(Controller):
	"""
	Implementation of a proportional controller which takes a position and returns a correcting velocity
	
	CONTROLLER:
	G(s) = K
	"""
		
	def __init__(self,_control,feedback_type,output_type,update_key,k,error_margin,hard_limit=1):
		# Set up controller parameters
		self.k = k

		# Initialise as Controller base class
		Controller.__init__(self, _control,feedback_type,output_type,update_key,error_margin,hard_limit)
		
	def heartbeat(self):
		# Debug heartbeat
		#print ("%s beat" % self.output_type)
		
		# Calculate output value
		error = self.r-self.y()
		psuedo_error = error * self.k
		correction = self.correction_step * psuedo_error
	
		# Continue as per Controller base class
		self.check_error(correction)
		self.output(correction)

class LeadLagController(Controller):
	"""
	Implementation of a lead-lag controller which takes a position and returns a correcting velocity
	Controller also pre-compensates by a value of K
	
	ANALOGUE CONTROLLER:
	G(s) = (as + 1) / (bs + 1)
	
	USE BACKWARD DIFFERENCE TRANSFORMATION:
		 z - 1
	s = -------
		  zT

	DIGITAL CONTORLLER:
			zT + (z-1)a
	G(z) =  ------------
			zT + (z-1)b
	
	DIFFERENCE EQUATION:
			  1
	y[k] =  -----  { (y[k-1] * b) - (e[k-1] * a) + (e[k] * (T+a)) }
			(T+b)
	"""

	def __init__(self,_control,feedback_type,output_type,update_key,k,a,b,T,error_margin,hard_limit=1):
		# Set up controller parameters
		self.a = a
		self.b = b
		self.T = T
		self.k = k

		# Set up calculation variables
		self.yk = 0		# y[k-1]
		self.e = [0,0]	# e[k-1],e[k]

		# Initialise as Controller base class
		Controller.__init__(self, _control,feedback_type,output_type,update_key,error_margin,hard_limit)
		
	def heartbeat(self):
		# Debug heartbeat
		#print ("%s beat" % self.output_type)
		
		# Update latest error with pre-compensation
		self.e[1] = self.k * (self.r - self.y())
		
		# Calculate y[k]
		part_1 = 1 / (self.T + self.b)
		part_2a = self.yk * self.b
		part_2b = self.e[0] * self.a
		part_2c = self.e[1] * (self.T + self.a)
		self.yk = part_1 * (part_2a - part_2b + part_2c)
		
		# Update error
		self.e[0] = self.e[1]
		
		# Continue as per Controller base class
		self.check_error(self.yk)
		self.output(self.yk)

class LeadLagController2(LeadLagController):
	"""
	Implementation of a lead-lag controller using Tustin Transformation. Takes a position and returns a correcting velocity
	Controller also pre-compensates by a value of K
	
	ANALOGUE CONTROLLER:
	G(s) = (as + 1) / (bs + 1)
	
	USE TUSTIN TRANSFORMATION:
		 2(z-1)
	s = --------
		 T(z+1)

	DIGITAL CONTORLLER:
			T(z+1) + 2(z-1)a
	G(z) =  ----------------
			T(z+1) + 2(z-1)b
	
	DIFFERENCE EQUATION:
			  1
	y[k] =  ------  { - (y[k-1]*(T-2b)) + (e[k-1]*(T-2a)) + (e[k]*(T+2a)) }
			(T+2b)
	"""

def heartbeat(self):
		# Debug heartbeat
		#print ("%s beat" % self.output_type)
		
		# Update latest error with pre-compensation
		self.e[1] = self.k * (self.r - self.y())
		
		# Calculate y[k]
		part_1 = 1 / (self.T + 2*self.b)
		part_2a = self.yk * (self.T - 2*self.b)
		part_2b = self.e[0] * (self.T - 2*self.a)
		part_2c = self.e[1] * (self.T + 2*self.a)
		self.yk = part_1 * (part_2b - part_2a + part_2c)
		
		# Update error
		self.e[0] = self.e[1]
		
		# Continue as per Controller base class
		self.check_error(self.yk)
		self.output(self.yk)
