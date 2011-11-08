"""An implementation of the control loop.

"""
import logging
log = logging.getLogger()

from . import atcommands as at
from . import navdata
from . import videopacket

class ConnectionError(Exception):
  """A class used to represent a connection error to the drone.
  
  """
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return str(self.value)

class ControlLoop(object):
  def __init__(self, connection, video_cb=None):
    """Initialse the control loop with a connection.

    You must call the connect and disconnect methods on the control loop before
    trying any control methods.

    Set video_cb to a callable which will be passed a sequence of bytes in
    RGB565 (==RGB16) format for each video frame.

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
    self._vid_decoder = videopacket.Decoder()
    self.video_cb = video_cb

    self._connection.navdata_cb = self._got_navdata

    # State for navdata
    self._last_navdata_sequence = 0
  
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
    OUTPUT: 'AT*FTRIM=1\r'
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
    OUTPUT: 'AT*CONFIG=1,"CONTROL:outdoor","FALSE"\rAT*REF=2,290718208\r'
    >>> cl.disconnect()

    """
    self._send(''.join([at.config('CONTROL:outdoor', False), at.ref(take_off = True)]))
  
  def land(self):
    r"""Send a land command.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> cl.connect()
    >>> cl.land()
    OUTPUT: 'AT*REF=1,290717696\r'
    >>> cl.disconnect()

    """
    self._send(at.ref(take_off = False, reset = False))
 
  def hover(self):
    r"""Send a hover command.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> cl.connect()
    >>> cl.hover()
    OUTPUT: 'AT*PCMD=1,1,0,0,0,0\r'
    >>> cl.disconnect()

    """
    self._send(at.pcmd())

  def reset(self):
    r"""Send a reset command to the drone.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)
    >>> cl.connect()
    >>> cl.reset()
    OUTPUT: 'AT*REF=1,290717952\r'
    >>> cl.disconnect()

    """
    self._send(at.ref(reset = True))

  def start_video(self):
    self._connection.viddata_cb = self._vid_decoder.decode
    self._vid_decoder.vid_cb = self.video_cb
    self._connection.put_video_packet('one')

  def start_navdata(self):
    log.info('starting navdata streaming')
    log.debug('Navdata booststrap stage 1');

    # See Dev. guide 7.1.2 pp. 40
    self._last_navdata_sequence = 0
    self._connection.put_navdata_packet('one')
    self._send(at.config('general:navdata_demo', True))

  def _got_navdata(self, data):
    ndh, packets = navdata.split(data)

    if not ndh.valid():
      log.error('Got invalid navdata packet')
      return

    # Dev. guide pp. 40: watchdog state
    watchdog_state = (ndh.state & navdata.ARDRONE_COM_WATCHDOG_MASK) != 0
    if watchdog_state:
      # this is a case where the sequence counter should be reset
      self._last_navdata_sequence = 0
      self._connection.put(at.comwdg())

    # Dev. guide pp. 40: lost communication
    lost_com = (ndh.state & navdata.ARDRONE_COM_LOST_MASK) != 0
    if lost_com:
      log.warning('Lost connection, re-establishing navdata connection.')
      self._last_navdata_sequence = 0
      self.start_navdata()

    if ndh.sequence <= self._last_navdata_sequence:
      log.error('Dropping out of sequence navdata packet: %s' % (ndh.sequence,))
      return

    # Record the sequence number
    self._last_navdata_sequence = ndh.sequence

    # Is the AR_DRONE_NAVDATA_BOOSTRAP status bit set (Dev. guide fig 7.1)
    if (ndh.state & navdata.ARDRONE_NAVDATA_BOOTSTRAP) != 0:
      log.debug('Navdata booststrap stage 2');
      self._send(at.config('general:navdata_demo', True))
      return

    # Is the ARDRONE_COMMAND_MASK bit set (Dev. guide fig 7.1)
    if (ndh.state & navdata.ARDRONE_COMMAND_MASK) != 0:
      # Send ACK
      log.debug('Navdata booststrap stage 3');
      self._send(at.ctrl(5))
      return

    print('state: %s' % (ndh.state,))
    print('Got data len: %s' % (len(data),))

  def _reset_sequence(self):
    at.reset_sequence()

  def _send(self, cmd):
    self._assert_connected()
    log.debug('Sending: %r' % (cmd,))
    self._connection.put(cmd)

  def _assert_connected(self):
    if not self.connected:
      raise ConnectionError('Not connected to drone.')
