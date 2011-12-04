"""
Central control loop
====================

An implementation of the control loop.

"""
import logging, json
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
  """A control loop for the drone. Initialises navdata and video streams.

  You must call the connect and disconnect methods on the control loop before
  trying any control methods.

  *host* is the IP address of the drone

  *control_host* is the IP address to which decoded packets will be sent

  *video_cb* is a callable which will be passed a sequence of bytes in
  RGB565 (==RGB16) format for each video frame.

  If non-None, navdata_cb is a callable which will be passed a block as
  defined in ardrone.core.navdata (e.g. DmoBlock, VisionDetectBlock, etc) as
  and when verified navdata packets arrive.

  >>> from ..platform import dummy
  >>> con = dummy.Connection()
  >>> cl = ControlLoop(con)

  """
  # Connection numbers
  _AT = 1
  _NAV = 2
  _VID = 3
  _CONTROL = 4
  _CONFIG = 5
  _CONTROL_DATA = 6
  _VIDEO_DATA = 7

  def __init__(self, connection,
      video_cb=None, navdata_cb=None,
      host='192.168.1.1', control_host='127.0.0.1',
      at_port=5556, nav_port=5554, vid_port=5555, config_port=5559,
      control_port=5560, control_data_port=5561,video_data_port=5562):

    self._connection = connection
    self._reset_sequence()
    self._vid_decoder = videopacket.Decoder()
    self._flying = False

    self.video_cb = video_cb
    self.navdata_cb = navdata_cb

    # State for navdata
    self._last_navdata_sequence = 0

    # State for control
    self._last_control_sequence = 0
    self._last_control_state = {
        'reset': False,
        'take_off': False,
        'roll': 0.0,
        'pitch': 0.0,
        'yaw': 0.0,
        'gas': 0.0,
        }

    # Open the connections
    self._connection.open(ControlLoop._AT, (host, at_port), (None, at_port, None))
    self._connection.open(ControlLoop._NAV, (host, nav_port), (None, nav_port, self._got_navdata))
    self._connection.open(ControlLoop._VID, (host, vid_port), (None, vid_port, self._got_video))
    self._connection.open(ControlLoop._CONTROL, (host, control_port), (None, control_port, self._got_control))
    self._connection.open(ControlLoop._CONFIG, (host, config_port), (None, config_port, self._got_config))
    self._connection.open(ControlLoop._CONTROL_DATA, (control_host, control_data_port), (None, 3456, None))
    self._connection.open(ControlLoop._VIDEO_DATA, (control_host, video_data_port), (None, 3457, None))
  
    self._config_to_send = []
  
  def bootstrap(self):
    """Initialise all the drone data streams."""
    log.info('Bootstrapping communication with the drone.')
    self.reset()
    self.flat_trim()
    #self.get_config()
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
    self._send(''.join([at.config('control:outdoor', False), at.ref(take_off = True)]))
  
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

  def start_video(self):
    self._connection.viddata_cb = self._vid_decoder.decode
    self._vid_decoder.vid_cb = self.video_cb
    self._connection.put(ControlLoop._VID, b'\x01\x00\x00\x00')

  def start_navdata(self):
    log.info('starting navdata streaming')
    log.debug('Navdata booststrap stage 1');

    # See Dev. guide 7.1.2 pp. 40
    self._last_navdata_sequence = 0
    self._connection.put(ControlLoop._NAV, b'\x01\x00\x00\x00')
    self.send_config()

  def _got_config(self, data):
    log.debug('Got config packet len: %s' % (len(data),))
    return

  def _got_navdata(self, data):
    ndh, packets = navdata.split(data)

    if not ndh.valid():
      log.error('Got invalid navdata packet')
      return

    # Dev. guide pp. 40: watchdog state
    watchdog_state = (ndh.state & navdata.ARDRONE_COM_WATCHDOG_MASK) != 0
    if watchdog_state:
      #log.info('Watchdog')
      # this is a case where the sequence counter should be reset
      self._last_navdata_sequence = 0
      self._connection.put(ControlLoop._AT, at.comwdg()) 

    #if (ndh.state & navdata.ARDRONE_COM_LOST_MASK) != 0:
    #  # Dev. guide pp. 40: lost communication
    #  log.warning('Lost connection, re-establishing navdata connection.')
    #  self._last_navdata_sequence = 0
    #  self.send_config()
    #  self.start_navdata()

    if (ndh.state & navdata.ARDRONE_NAVDATA_BOOTSTRAP) != 0:
      # Is the AR_DRONE_NAVDATA_BOOSTRAP status bit set (Dev. guide fig 7.1)
      log.debug('Navdata booststrap')
      self.send_config()
      key, value = self._config_to_send[0]
      log.info('Sending: %s = %s' % (key, value))
      self._send(at.config(key, value))

    if (ndh.state & navdata.ARDRONE_COMMAND_MASK) != 0:
      log.debug('ACK command')
      self._send(at.ctrl(5))
      self._config_to_send = self._config_to_send[1:]

    if len(self._config_to_send) > 0:
      key, value = self._config_to_send[0]
      log.debug('Sending: %s = %s' % (key, value))
      self._send(at.config(key, value))

    if ndh.sequence <= self._last_navdata_sequence:
      log.error('Dropping out of sequence navdata packet: %s' % (ndh.sequence,))
      return

    # Record the sequence number
    self._last_navdata_sequence = ndh.sequence

    # Record flying state
    self._flying = (ndh.state & navdata.ARDRONE_FLY_MASK) != 0

    for packet in packets:
      # Send a JSON encoded control packet to the controller
      self._connection.put(ControlLoop._CONTROL_DATA, packet.json())

      # Call the navdata callable if one is configured
      if self.navdata_cb is not None:
        self.navdata_cb(packet)

  def send_config(self):
#    self._config_to_send.append(('general:navdata_demo', True))
    self._config_to_send.append(('general:navdata_demo', False)) # required for video detect
    self._config_to_send.append(('video:video_channel', 2))    
    #self._config_to_send.append(('video:video_bitrate_control_mode', '1')) # Dynamic
    #self._config_to_send.append(('video:video_codec', '64'))
    self._config_to_send.append(('general:vision_enable', True))
    self._config_to_send.append(('detect:detect_type', 2))
    self._config_to_send.append(('detect:enemy_colors', 2)) # orange-yellow-orange 
    self._config_to_send.append(('detect:detections_select_h', 1))
    self._config_to_send.append(('detect:enemy_without_shell', False))

  def _got_config(self, packet):
    log.info('Got config len %i' % (len(packet),))

  def _got_video(self, packet):
    self._connection.put(ControlLoop._VIDEO_DATA, packet)
    self._vid_decoder.decode(packet) #comment this out when done elsewhere

  def _got_control(self, packet):
    # log.debug('Got control packet: %r' % (packet,))

    # Parse packet
    data = json.loads(packet.decode())

    # Reset sequence counter if we get a '1'
    if data['seq'] == 1:
      self._last_control_sequence = 0

    # Check and update sequence counter
    if data['seq'] <= self._last_control_sequence:
      log.warning('Dropping control packet with invalid sequence number: %i' % (data.seq,))
      return
    self._last_control_sequence = data['seq']

    # Extract control state
    state = data['state']
    #log.debug('Control state: %r' % (state,))

    # Compare state to recorded state
    if not self._last_control_state['reset'] and state['reset']:
      self.bootstrap()
    if not self._last_control_state['take_off'] and state['take_off']:
      if self._flying:
        self.land()
      else:
        self.take_off()

    # Send the command state
    self._send(at.pcmd(not state['hover'], False, state['roll'], state['pitch'], state['gas'], state['yaw']))

    # Record this state
    self._last_control_state = state

  def _reset_sequence(self):
    at.reset_sequence()

  def _send(self, cmd):
    log.debug('Sending: %r' % (cmd,))
    self._connection.put(ControlLoop._AT, cmd)
