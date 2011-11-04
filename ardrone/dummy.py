"""A dummy connection for testing.

"""

import random
import threading

import connection

class Connection(connection.Connection):
	r""" A simple test connection which can be used to develop applications.

	This connection object doesn't actually connect to the drone. Instead it can
	be used to 'fake' a drone sending navpackets. Commands sent *to* the drone
	are logged by an optional logging function.

	For example:

	>>> import atcommands as at
	>>> at.reset_sequence()
	>>> a = Connection()
	>>> a.put(at.ref())
	OUTPUT: 'AT*REF=1,290717696\n'
	>>> b = Connection(log_cb = lambda x: print('Log: %s' % (repr(x),)))
	>>> b.put(at.ref())
	Log: 'AT*REF=2,290717696\n'

	"""

	def __init__(self, log_cb = None, data_cb = None, *args, **kwargs):
		connection.Connection.__init__(self, *args, **kwargs)

		""" Create the dummy connection object.

		data_cb is a callable which will periodically be sent fake navdata packets.

		>>> a = Connection()
		>>> a._data_cb is None
		True
		>>> p = None
		>>> def foo(packet):
		...		global p
		...		p = packet
		>>> p is None
		True
		>>> b = Connection(data_cb = foo)
		>>> b._data_cb is None
		False
		>>> b._data_cb is foo
		True
		>>> import time
		>>> time.sleep(2)
		>>> p is None
		False

		"""
		self._data_cb = data_cb
		self._log_cb = log_cb
		self._schedule_cb('Hello')

	def put(self, command_string):
		r""" Send the command string to the drone over the network.

		>>> import atcommands as at
		>>> t = Connection()
		>>> t.put('Foo\nBar')
		OUTPUT: 'Foo\nBar'
		>>> at.reset_sequence()
		>>> t.put(at.ref())
		OUTPUT: 'AT*REF=1,290717696\n'
		>>> t.put(at.ref())
		OUTPUT: 'AT*REF=2,290717696\n'
		"""

		if self._log_cb is None:
			print('OUTPUT: %s' % (repr(str(command_string)),))
		else:
			self._log_cb(str(command_string))
	
	def _schedule_cb(self, data):
		if self._data_cb is None:
			return
		t = threading.Timer(random.random() + 0.05, lambda: self._data_cb(data))
		t.start()

if __name__ == '__main__':
	import doctest
	doctest.testmod()
