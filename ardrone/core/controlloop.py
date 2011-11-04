"""An implementation of the control loop.

"""

from . import atcommands as at

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

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> try:
    ...   cl.disconnect()
    ... except ConnectionError:
    ...   print('Not connected')
    Not connected
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
    self._reset_sequence()
  
  def connect(self):
    self.connected = self._connection.connect()
    self._assert_connected()
  
  def disconnect(self):
    self._assert_connected()
    self._connection.disconnect()
    self.connected = False

  def flat_trim(self):
    r"""Send a take off command.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> cl.connect()
    >>> cl.flat_trim()
    OUTPUT: 'AT*FTRIM=1\n'
    >>> cl.disconnect()

    """
    self._send(at.ftrim())

  def take_off(self):
    r"""Send a take off command.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> cl.connect()
    >>> cl.take_off()
    OUTPUT: 'AT*REF=1,290718208\n'
    >>> cl.disconnect()

    """
    self._send(at.ref(take_off = True))
  
  def land(self):
    r"""Send a land command.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> cl.connect()
    >>> cl.land()
    OUTPUT: 'AT*REF=1,290717696\n'
    >>> cl.disconnect()

    """
    self._send(at.ref(take_off = False, reset = False))

  def reset(self):
    r"""Send a reset command to the drone.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> cl.connect()
    >>> cl.reset()
    OUTPUT: 'AT*REF=1,290717952\n'
    >>> cl.disconnect()

    """
    self._send(at.ref(reset = True))

  def _reset_sequence(self):
    at.reset_sequence()

  def _send(self, cmd):
    self._assert_connected()
    self._connection.put(cmd)

  def _assert_connected(self):
    if not self.connected:
      raise ConnectionError('Not connected to drone.')
