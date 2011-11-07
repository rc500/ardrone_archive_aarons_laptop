"""Functions to generate AT commands for the A.R. Drone.

This module provides various API functions to generate AT commands for sending
to an A.R. drone. For example, to lift off and set hover mode:

>>> reset_sequence()
>>> ''.join([ref(reset = True), pcmd(False), ref(take_off = True)])
'AT*REF=1,290717952\\nAT*PCMD=2,0,0,0,0,0\\nAT*REF=3,290718208\\n'

In general the sequence number will be incremented automatically for you
although one can use reset_sequence to set it back to 1.

"""

import ctypes as ct

# The common prefix for all AT commands
__prefix = 'AT*'

# The <LF> (line feed) string.
__lf = '\r'

__sequence = 0

def reset_sequence():
  """Internally AT commands have a sequence number. The drone expects the first
  command to have sequence number 1 and the remaining commands to increase in
  number (see developer guide). This function resets the sequence counter back
  to 1.

  """
  global __sequence
  __sequence = 0

def ref(reset = False, take_off = False):
  """Generate the (take off/land) (emergency/reset) AT*REF command.

  >>> reset_sequence()
  >>> ref()
  'AT*REF=1,290717696\\n'
  >>> ref(True, False)
  'AT*REF=2,290717952\\n'
  >>> ref(False, True)
  'AT*REF=3,290718208\\n'
  >>> ref(reset = True)
  'AT*REF=4,290717952\\n'
  >>> ref(take_off = True)
  'AT*REF=5,290718208\\n'

  """
  v = 0x11540000 # randomly a few bits need to be set
  if reset:
    v |= (1 << 8)
  if take_off:
    v |= (1 << 9)
  return __at('REF', ct.c_int32(v))

def pcmd(progressive_commands = True, combined_yaw = False,
    left_right_tilt = 0.0, front_back_tilt = 0.0,
    vertical_speed = 0.0, angular_speed = 0.0):
  """Generate a PCMD AT Command sequence.

  >>> reset_sequence()
  >>> pcmd()
  'AT*PCMD=1,1,0,0,0,0\\n'
  >>> pcmd(False, True)
  'AT*PCMD=2,2,0,0,0,0\\n'
  >>> pcmd(left_right_tilt = -0.5)
  'AT*PCMD=3,1,-1090519040,0,0,0\\n'
  >>> pcmd(left_right_tilt = 1.0)
  'AT*PCMD=4,1,1065353216,0,0,0\\n'
  >>> pcmd(left_right_tilt = 2.0)
  'AT*PCMD=5,1,1065353216,0,0,0\\n'
  >>> pcmd(front_back_tilt = -0.8)
  'AT*PCMD=6,1,0,-1085485875,0,0\\n'
  >>> pcmd(front_back_tilt = -1.0)
  'AT*PCMD=7,1,0,-1082130432,0,0\\n'
  >>> pcmd(vertical_speed = -0.8)
  'AT*PCMD=8,1,0,0,-1085485875,0\\n'
  >>> pcmd(angular_speed = -0.8)
  'AT*PCMD=9,1,0,0,0,-1085485875\\n'

  """

  flag = 0
  if progressive_commands:
    flag |= (1 << 0)
  if combined_yaw:
    flag |= (1 << 1)
  
  left_right_tilt = min(1.0, max(-1.0, left_right_tilt))
  front_back_tilt = min(1.0, max(-1.0, front_back_tilt))
  vertical_speed = min(1.0, max(-1.0, vertical_speed))
  angular_speed = min(1.0, max(-1.0, angular_speed))

  return __at('PCMD', ct.c_int32(flag),
      ct.c_float(left_right_tilt),
      ct.c_float(front_back_tilt),
      ct.c_float(vertical_speed),
      ct.c_float(angular_speed))

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

def config_ids(session_id, user_id, application_id):
  """Generate the CONFIG_IDS AT command.

  >>> reset_sequence()
  >>> config_ids('session_id', 'user_id', 'application_id')
  'AT*CONFIG_IDS=1,"session_id","user_id","application_id"\\n'

  """
  return __at('CONFIG_IDS', str(session_id), str(user_id), str(application_id))

def comwdg():
  """Generate the COMWGD AT command to reset the watchdog.

  >>> reset_sequence()
  >>> comwdg()
  'AT*COMWDG=1\\n'

  """
  return __at('COMWDG')

def ctrl(mode):
  """Generate the CTRL AT command.

  >>> reset_sequence()
  >>> ctrl(4)
  'AT*CTRL=1,4\\n'

  """
  return __at('CTRL', ct.c_int32(mode))

def __next_sequence():
  """Return the next sequence number for the AT command.

  >>> reset_sequence()
  >>> __next_sequence().value
  1
  >>> __next_sequence().value
  2
  >>> __next_sequence().value
  3
  >>> reset_sequence()
  >>> __next_sequence().value
  1
  >>> import ctypes as ct
  >>> isinstance(__next_sequence(), ct.c_int32)
  True

  """
  global __sequence
  __sequence += 1
  return ct.c_int32(__sequence)

def __at(name, *args):
  """Format an entire AT string.

  >>> import ctypes
  >>> def i(x):
  ...   return ct.c_int32(x)
  >>> reset_sequence()
  >>> __at('PCMD', i(1), i(0), i(0), i(0), i(0))
  'AT*PCMD=1,1,0,0,0,0\\n'
  >>> __at('PCMD', i(1), i(0), i(0), i(0), i(0))
  'AT*PCMD=2,1,0,0,0,0\\n'
  >>> reset_sequence()
  >>> __at('PCMD', i(1), i(0), i(0), i(0), i(0))
  'AT*PCMD=1,1,0,0,0,0\\n'
  >>> __at('PCMD')
  'AT*PCMD=2\\n'

  """
  return '%s%s=%s%s' % (__prefix, name, __format_arg([__next_sequence()] + list(args)), __lf)

def __format_arg(a):
  """Format an argument suitably for embedding in an AT command.

  The argument must be a string, ct.c_int32, ct.c_float or a
  sequence of any valid argument to __format_arg(). A sequence will be
  flattened into a comma-semarated list of the elements which have each
  been formatted by __format_arg().

  >>> import ctypes as ct
  >>> __format_arg(ct.c_int32(4))
  '4'
  >>> __format_arg('hello')
  '"hello"'
  >>> __format_arg(ct.c_float(-0.8))
  '-1085485875'
  >>> __format_arg(ct.c_float(-1.0))
  '-1082130432'
  >>> __format_arg([ct.c_int32(x) for x in [1,2,3]])
  '1,2,3'
  >>> __format_arg((ct.c_int32(1),ct.c_int32(4)))
  '1,4'
  >>> __format_arg((ct.c_int32(1),))
  '1'
  >>> __format_arg([ct.c_int32(1),'hello',ct.c_float(-0.8)])
  '1,"hello",-1085485875'
  >>> import re
  >>> __format_arg(re) # doctest: +ELLIPSIS
  Traceback (most recent call last):
    File "<stdin>", line 1, in ?
  TypeError: Argument must be a sequence, string, c_int32 or c_float (got ...

  """

  # stringy
  if isinstance(a, str):
    return '"'+a+'"'

  # try a floating point
  if isinstance(a, ct.c_float):
    # These are some dirty tricks using the ctypes pointer munging abilities
    pcf = ct.byref(a)
    pci = ct.cast(pcf, ct.POINTER(ct.c_int32))
    return '%d' % (pci[0],)

  # try an integer
  if isinstance(a, ct.c_int32):
    return '%d' % (a.value,)

  # last hope, sequence
  if hasattr(a, '__iter__'):
    return ','.join([__format_arg(x) for x in a])

  raise TypeError('Argument must be a sequence, string, c_int32 or c_float (got %s)' % (repr(a),))
