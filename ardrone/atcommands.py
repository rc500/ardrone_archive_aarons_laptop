"""
"""

import numpy as np

__prefix = 'AT*'
__lf = '\x0a'

__sequence = 0

def reset_sequence():
	"""Internally AT commands have a sequence number. The drone expects the first
	command to have sequence number 1 and the remaining commands to increase in
	number (see developer guide). This function resets the sequence counter back
	to 1.

	"""
	global __sequence
	__sequence = 0

def ref(emergency = False, take_off = False):
	"""Generate the (take off/land) (emergency/reset) AT*REF command.

	>>> reset_sequence()
	>>> ref()
	'AT*REF=1,290717696\\n'
	>>> ref(True, False)
	'AT*REF=2,290717952\\n'
	>>> ref(False, True)
	'AT*REF=3,290718208\\n'
	>>> ref(emergency = True)
	'AT*REF=4,290717952\\n'
	>>> ref(take_off = True)
	'AT*REF=5,290718208\\n'

	"""
	v = 0x11540000 # randomly a few bits need to be set
	if emergency:
		v |= (1 << 8)
	if take_off:
		v |= (1 << 9)
	return __at('REF', v)

def ftrim():
	"""Generate the FTRIM AT command.

	>>> reset_sequence()
	>>> ftrim()
	'AT*FTRIM=1\\n'
	>>> ftrim()
	'AT*FTRIM=2\\n'

	"""
	return __at('FTRIM')

def config(key, value):
	"""Generate the CONFIG AT command.

	>>> reset_sequence()
	>>> config('GENERAL:num_version_config', 1)
	'AT*CONFIG=1,"GENERAL:num_version_config","1"\\n'
	>>> config('GENERAL:vision_enable', True)
	'AT*CONFIG=2,"GENERAL:vision_enable","TRUE"\\n'
	>>> config('GENERAL:gyros_gains', '{ 6.9026551e-03 -6.9553638e-03 -3.8592720e-03 }')
	'AT*CONFIG=3,"GENERAL:gyros_gains","{ 6.9026551e-03 -6.9553638e-03 -3.8592720e-03 }"\\n'

	"""
	if isinstance(value, bool):
		if value:
			value = 'TRUE'
		else:
			value = 'FALSE'
	return __at('CONFIG', str(key), str(value))

def __next_sequence():
	"""Return the next sequence number for the AT command.

	>>> reset_sequence()
	>>> __next_sequence()
	1
	>>> __next_sequence()
	2
	>>> __next_sequence()
	3
	>>> reset_sequence()
	>>> __next_sequence()
	1

	"""
	global __sequence
	__sequence += 1
	return __sequence

def __at(name, *args):
	"""Format an entire AT string.

	>>> reset_sequence()
	>>> __at('PCMD', 1, 0, 0, 0, 0)
	'AT*PCMD=1,1,0,0,0,0\\n'
	>>> __at('PCMD', 1, 0, 0, 0, 0)
	'AT*PCMD=2,1,0,0,0,0\\n'
	>>> reset_sequence()
	>>> __at('PCMD', 1, 0, 0, 0, 0)
	'AT*PCMD=1,1,0,0,0,0\\n'
	>>> __at('PCMD')
	'AT*PCMD=2\\n'

	"""
	return '%s%s=%s%s' % (__prefix, name, __format_arg([__next_sequence()] + list(args)), __lf)

def __format_arg(a):
	"""Format an argument suitably for embedding in an AT command.

	>>> __format_arg(4)
	'4'
	>>> __format_arg('hello')
	'"hello"'
	>>> __format_arg(-0.8)
	'-1085485875'
	>>> __format_arg(-1.0)
	'-1082130432'
	>>> __format_arg([1,2,3])
	'1,2,3'
	>>> __format_arg((1,2,3))
	'1,2,3'
	>>> __format_arg((1,))
	'1'
	>>> __format_arg([1,'hello',-0.8])
	'1,"hello",-1085485875'
	>>> __format_arg(np)
	Traceback (most recent call last):
	  File "<stdin>", line 1, in ?
	TypeError: Argument must be a sequence, string, integer or float

	"""

	# stringy
	if isinstance(a, str):
		return '"%s"' % (a,)

	# try a floating point
	if isinstance(a, float):
		bs = np.array([a], dtype=np.float32).data
		return __format_arg(int(np.frombuffer(bs, dtype=np.int32)[0]))

	# try an integer
	try:
		if int(a) == a:
			return '%d' % (a,)
	except TypeError:
		pass

	# last hope, sequence
	try:
		return ','.join([__format_arg(x) for x in a])
	except TypeError:
		pass

	raise TypeError('Argument must be a sequence, string, integer or float')

if __name__ == "__main__":
    import doctest
    doctest.testmod()
