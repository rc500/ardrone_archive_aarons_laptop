"""An implementation of the control loop.

"""

import ardrone.atcommands as at

class ConnectionError(Exception):
	"""A class used to represent a connection error to the drone.
	
	"""
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return str(self.value)

class ControlLoop(object):
	def __init__(self, connection):
		"""Initialse the control loop with a connection.

		You must call the connect and disconnect methods on the control loop before
		trying any control methods.

		>>> import ardrone.dummy
		>>> con = ardrone.dummy.Connection()
		>>> cl = ControlLoop(con)
		>>> cl.disconnect()
		Traceback (most recent call last):
		  File "<stdin>", line 1, in ?
		controlloop.ConnectionError: Not connected to drone.
		>>> cl.connected
		False
		>>> cl.connect()
		>>> cl.connected
		True
		>>> cl.disconnect()
		>>> cl.connected
		False

		"""
		self.connected = False
		self._connection = connection
	
	def connect(self):
		self.connected = self._connection.connect()
		self._assert_connected()
	
	def disconnect(self):
		self._assert_connected()
		self._connection.disconnect()
		self.connected = False
	
	def reset(self):
		r"""Send a reset command to the drone.

		>>> import ardrone.dummy
		>>> con = ardrone.dummy.Connection()
		>>> cl = ControlLoop(con)
		>>> cl.connect()
		>>> cl.reset()
		OUTPUT: 'AT*REF=1,290717952\n'
		>>> cl.disconnect()

		"""
		self._send(at.ref(reset = True))

	def _send(self, cmd):
		self._assert_connected()
		self._connection.put(cmd)

	def _assert_connected(self):
		if not self.connected:
			raise ConnectionError('Not connected to drone.')
