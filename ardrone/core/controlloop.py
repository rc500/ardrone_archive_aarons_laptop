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
  """A control loop.

  """

  # Connection numbers
  _AT = 1
  _NAV = 2
  _VID = 3

  def __init__(self, connection,
      video_cb=None, navdata_cb=None,
      host='192.168.1.1',
      at_port=5556, nav_port=5554, vid_port=5555, config_port=5559):
    """Initialse the control loop with a connection.

    You must call the connect and disconnect methods on the control loop before
    trying any control methods.

    Set video_cb to a callable which will be passed a sequence of bytes in
    RGB565 (==RGB16) format for each video frame.

    If non-None, navdata_cb is a callable which will be passed a block as
    defined in ardrone.core.navdata (e.g. DmoBlock, VisionDetectBlock, etc) as
    and when verified navdata packets arrive.

    >>> from ..platform import dummy
    >>> con = dummy.Connection()
    >>> cl = ControlLoop(con)

    """
    self._connection = connection
    self._reset_sequence()
    self._vid_decoder = videopacket.Decoder()

    self.video_cb = video_cb
    self.navdata_cb = navdata_cb

    # State for navdata
    self._last_navdata_sequence = 0

    # Open the connections
    self._connection.open(ControlLoop._AT, (host, at_port), (None, at_port, None))
    self._connection.open(ControlLoop._NAV, (host, nav_port), (None, nav_port, self._got_navdata))
    self._connection.open(ControlLoop._VID, (host, vid_port), (None, vid_port, None))
  
  def bootstrap(self):
    """Initialise all the drone data streams."""
    log.info('Bootstrapping communication with the drone.')
    self.reset()
    self.flat_trim()
    self.get_config()
    self.start_navdata()
    self.start_video()

  def get_config(self):
    """Ask the drone for it's configuration."""
    log.info('Requesting configuration from drone.')
    self._send(at.ctrl(4))

  def flat_trim(self):
    r"""Send a take off command.

    """
    self._send(at.ftrim())

  def take_off(self):
    r"""Send a take off command.

    """
    self._send(''.join([at.config('CONTROL:outdoor', False), at.ref(take_off = True)]))
  
  def land(self):
    r"""Send a land command.

    """
    self._send(at.ref(take_off = False, reset = False))
 
  def hover(self):
    r"""Send a hover command.

    """
    self._send(at.pcmd())

  def reset(self):
    r"""Send a reset command to the drone.

    """
    self._send(at.ref(reset = True))
    #self._send(at.config('video:video_bitrate_control_mode', '1'))
    #self._send(at.config('video:video_bitrate', '2000'))
    #self._send(at.config('video:video_codec', '32'))

  def start_video(self):
    self._connection.viddata_cb = self._vid_decoder.decode
    self._vid_decoder.vid_cb = self.video_cb
    self._connection.put(ControlLoop._VID, 'one')

  def start_navdata(self):
    log.info('starting navdata streaming')
    log.debug('Navdata booststrap stage 1');

    # See Dev. guide 7.1.2 pp. 40
    self._last_navdata_sequence = 0
    self._connection.put(ControlLoop._NAV, 'one')
    self._send(at.config('general:navdata_demo', True))

  def _got_config(self, data):
    log.info('Got config packet len: %s' % (len(data),))
    return

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
      self._connection.put(ControlLoop._AT, at.comwdg())

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

    for packet in packets:
      if self.navdata_cb is not None:
        self.navdata_cb(packet)

      #if isinstance(packet, navdata.DemoBlock):
      #  log.info('Battery: %i' % (packet.vbat_flying_percentage,))
      #  log.info('Orientation: %f,%f,%f' % (packet.theta, packet.phi, packet.psi))
      #  log.info('Altitude: %i' % (packet.altitude,))

    #print('state: %s' % (ndh.state,))
    #print('Got data len: %s' % (len(data),))

  def _reset_sequence(self):
    at.reset_sequence()

  def _send(self, cmd):
    log.debug('Sending: %r' % (cmd,))
    self._connection.put(ControlLoop._AT, cmd)
