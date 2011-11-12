"""Functions to generate AT commands for the A.R. Drone.

This module is based on chapter 6 of the developer guie (pp.29). Most direct
control of the drone is accomplished by sending UDP packets containing
so-called 'AT' commands to the drone on port 5559. This module wraps functions
to generate AT command strings along with some internal utility functions to
provide the ppropriate floating-point -> integer conversion.

Each public AT command function in this module takes a set of keyword arguments
and returns an appropriately encoded AT command for sending directly to the
dron. For example, to lift off and set hover mode:

>>> reset_sequence()
>>> ''.join([ref(reset = True), pcmd(False), ref(take_off = True)])
'AT*REF=1,290717952\\rAT*PCMD=2,0,0,0,0,0\\rAT*REF=3,290718208\\r'

"""

"""We make use of the ctypes module primarily to allow for the floating point
-> integer conversion required by the AT commands. In addition, we explicitly
encode all AT command parameters as _machine_ types such as c_int or c_float
rather than Python types such as int or float. This is because commands sent to
the drone require/assume that they are backed by a particular binary encoding
which Python hids from you for its built in types.

"""
import ctypes as ct

"""All AT commands start with a common prefix: (dev. guide 6.1, pp. 30)"""
__prefix = 'AT*'

"""All AT commands end with a common suffix: (dev. guide 6.1, pp. 30)"""
__lf = '\r'

"""AT commands are sent to the drone with an associated sequence number. The
drone will ignore commands sent to it with a sequence number less than or equal
to one it has alreay received (dev. guide 6.2, pp. 30). We keep track of this
sequence number as a global counter since we assume one process is controlling
one drone.

It may well be required for future expansion that this state be abstracted into
a class. For the moment, owever, this is sufficient for our purposes.

"""
__sequence = 0

def reset_sequence():
  """Internally AT commands have a sequence number. The drone expects the first
  command to have sequence number 1 and the remaining commands to increase in
  number (see dev. guide 6.2, pp. 30). We maintain a global sequence number
  countin __sequence. This function resets the sequence counter back to 1.

  """
  global __sequence
  __sequence = 0

def ref(reset = False, take_off = False):
  """Control basic behaviour of the drone: take-off/land and emergency/reset.
  
  See: Dev. guide: 6.6, pp. 33.

  >>> reset_sequence()
  >>> ref()
  'AT*REF=1,290717696\\r'
  >>> ref(True, False)
  'AT*REF=2,290717952\\r'
  >>> ref(False, True)
  'AT*REF=3,290718208\\r'
  >>> ref(reset = True)
  'AT*REF=4,290717952\\r'
  >>> ref(take_off = True)
  'AT*REF=5,290718208\\r'

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
  """Control motion of the drone and activate/de-activate auto-hover mode.
  
  See: Dev. guide: 6.6, pp. 35.

  The PCMD command controls at least three features:

  - Progressive commands: if enabled, roll, pitch, yaw and vertical speed (gas)
    will be honoured by the drone. If disabled, the drone will attempt to hover
    in one spot autonomously.

  - Combined yaw: if enabled, angular speed changed will result in a combined
    yaw and roll (a 'racing' turn) which may be more efficient at high speed.

  - The left/right and front/back tilt commands are floating point values in
    the range [-1,1]. They reflect a proportion of the maximum tilt angle the
    drone is configured to perform. The vertical speed and angular speed
    reflect the commanded speed rather than actual value. The units are
    unknown.

  >>> reset_sequence()
  >>> pcmd()
  'AT*PCMD=1,1,0,0,0,0\\r'
  >>> pcmd(False, True)
  'AT*PCMD=2,2,0,0,0,0\\r'
  >>> pcmd(left_right_tilt = -0.5)
  'AT*PCMD=3,1,-1090519040,0,0,0\\r'
  >>> pcmd(left_right_tilt = 1.0)
  'AT*PCMD=4,1,1065353216,0,0,0\\r'
  >>> pcmd(left_right_tilt = 2.0)
  'AT*PCMD=5,1,1065353216,0,0,0\\r'
  >>> pcmd(front_back_tilt = -0.8)
  'AT*PCMD=6,1,0,-1085485875,0,0\\r'
  >>> pcmd(front_back_tilt = -1.0)
  'AT*PCMD=7,1,0,-1082130432,0,0\\r'
  >>> pcmd(vertical_speed = -0.8)
  'AT*PCMD=8,1,0,0,-1085485875,0\\r'
  >>> pcmd(angular_speed = -0.8)
  'AT*PCMD=9,1,0,0,0,-1085485875\\r'

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
  """Set 'flat trim', i.e. calibrate the drone's idea of what is horizontal.
  
  See: Dev. guide: 6.6, pp. 36.

  The flat trim datum is the orientation of the drone when left/right and
  front/back tilts are set to 0. It is also (it would appear) used within the
  autonomous hover control-loop.

  The drone appears to use whatever it's orientation is the _moment_ the power
  is connected as this initial datum. Since one is usually holding the drone at
  this point, it is generally a good idea to send this command to the drone
  just before taking off. Failing to do this tends to lead to the drone flying
  off in one direction.

  >>> reset_sequence()
  >>> ftrim()
  'AT*FTRIM=1\\r'
  >>> ftrim()
  'AT*FTRIM=2\\r'

  """
  return __at('FTRIM')

def config(key, value):
  """Set configuration values for the drone.
  
  See: Dev. guide: 6.6, pp. 37.

  The drone has a number of configuration commands which my be configured. See
  dev. guide ch. 8, pp. 59. This command will set a specfied configuration
  parameter.

  ''Note'' I've not ascertained whether these _actually work_ yet.

  >>> reset_sequence()
  >>> config('GENERAL:num_version_config', 1)
  'AT*CONFIG=1,"GENERAL:num_version_config","1"\\r'
  >>> config('GENERAL:vision_enable', True)
  'AT*CONFIG=2,"GENERAL:vision_enable","TRUE"\\r'
  >>> config('GENERAL:gyros_gains', '{ 6.9026551e-03 -6.9553638e-03 -3.8592720e-03 }')
  'AT*CONFIG=3,"GENERAL:gyros_gains","{ 6.9026551e-03 -6.9553638e-03 -3.8592720e-03 }"\\r'

  """
  if isinstance(value, bool):
    if value:
      value = 'TRUE'
    else:
      value = 'FALSE'
  return __at('CONFIG', str(key), str(value))

def config_ids(session_id, user_id, application_id):
  """Generate the CONFIG_IDS AT command to set identification for the next
  configuration command.
  
  See: Dev. guide: 6.6, pp. 37.

  ''Note'' I haven't tested this command yet.

  >>> reset_sequence()
  >>> config_ids('session_id', 'user_id', 'application_id')
  'AT*CONFIG_IDS=1,"session_id","user_id","application_id"\\r'

  """
  return __at('CONFIG_IDS', str(session_id), str(user_id), str(application_id))

def comwdg():
  """Reset the connection lost watchdog state.

  See: Dev. guide: 6.6, pp. 37, 7.1.2, pp. 40.

  When handshaking with the drone to make it report navigation data via navdata
  packets, the client must detect when the drone enters it's 'watchdog state'.
  The drone will do this when it suspects communication with the client has
  been lost. When this state has been detected, the COMWDG command must be sent
  to the drone to reset the watchdog.

  See ardrone.core.controlloop for more details.

  >>> reset_sequence()
  >>> comwdg()
  'AT*COMWDG=1\\r'

  """
  return __at('COMWDG')

def ctrl(mode, filesize=0):
  """Generate the CTRL AT command.

  This command is undocumented and has been derrived by looking at the SDK
  source code.

  It would appear that this command is a miscellaneous 'catch all' command for
  toggling state. As I understand it more, I'll add documentation here.

  >>> reset_sequence()
  >>> ctrl(4)
  'AT*CTRL=1,4,0\\r'

  """
  return __at('CTRL', ct.c_int32(mode), ct.c_int32(filesize))

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
  'AT*PCMD=1,1,0,0,0,0\\r'
  >>> __at('PCMD', i(1), i(0), i(0), i(0), i(0))
  'AT*PCMD=2,1,0,0,0,0\\r'
  >>> reset_sequence()
  >>> __at('PCMD', i(1), i(0), i(0), i(0), i(0))
  'AT*PCMD=1,1,0,0,0,0\\r'
  >>> __at('PCMD')
  'AT*PCMD=2\\r'

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

