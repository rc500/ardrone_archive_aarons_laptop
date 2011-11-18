"""
Parsing ``navdata`` packets from the drone
------------------------------------------

.. warning:: The majority of code in this module has been reverse engineered
  from the SDK. It relies heavily on undocumented features.

See dev. guide ch. 7, pp 39.

Python isn't really geared up to parse in-memory data structures in the same
way that C is. Fortunately the ctypes module allows Python to do this without
too much pain. What pain _is_ required is wrapped into this module.

_Unfortunately_ the navdata stream is almost entirely undocumented in the
developers' guide. The knowledge crystalised in this module, therefore, has
been obtained by directly reading the various navdata.c source files in the
SDK.

Since the packet format is undocumented beyond how to parse the option block
header, things in this module are subject to change.

Each block as returned from the drone has a json() method which may be used to
get a JSON formatted string describing the block.

"""

"""We use the veneabe ctypes module for parsing in-memory data structures."""
import ctypes as ct

# Use the logging module to log any errors/warnings.
import logging
log = logging.getLogger()

import json

"""The header for a navdata packet. (Dev. guide 7.1.1, pp. 39)"""
NAVDATA_HEADER = ct.c_int32(0x55667788)

"""The navdata demo tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_DEMO_TAG = ct.c_int16(0)

"""The navdata vision detect tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_VISION_DETECT_TAG = ct.c_int16(16)

"""The navdata 'iPhone angles' tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_IPHONE_ANGLES_TAG = ct.c_int16(18)

"""The navdata checksum tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_CKS_TAG = ct.c_int16(0xffff)

# Define masks for ARDrone state
# 31                                                             0
#  x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x -> state
#  | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | |
#  | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | FLY MASK : (0) ardrone is landed, (1) ardrone is flying
#  | | | | | | | | | | | | | | | | | | | | | | | | | | | | | | VIDEO MASK : (0) video disable, (1) video enable
#  | | | | | | | | | | | | | | | | | | | | | | | | | | | | | VISION MASK : (0) vision disable, (1) vision enable
#  | | | | | | | | | | | | | | | | | | | | | | | | | | | | CONTROL ALGO : (0) euler angles control, (1) angular speed control
#  | | | | | | | | | | | | | | | | | | | | | | | | | | | ALTITUDE CONTROL ALGO : (0) altitude control inactive (1) altitude control active
#  | | | | | | | | | | | | | | | | | | | | | | | | | | USER feedback : Start button state
#  | | | | | | | | | | | | | | | | | | | | | | | | | Control command ACK : (0) None, (1) one received
#  | | | | | | | | | | | | | | | | | | | | | | | | Trim command ACK : (0) None, (1) one received
#  | | | | | | | | | | | | | | | | | | | | | | | Trim running : (0) none, (1) running
#  | | | | | | | | | | | | | | | | | | | | | | Trim result : (0) failed, (1) succeeded
#  | | | | | | | | | | | | | | | | | | | | | Navdata demo : (0) All navdata, (1) only navdata demo
#  | | | | | | | | | | | | | | | | | | | | Navdata bootstrap : (0) options sent in all or demo mode, (1) no navdata options sent
#  | | | | | | | | | | | | | | | | | | | | Motors status : (0) Ok, (1) Motors Com is down
#  | | | | | | | | | | | | | | | | | |
#  | | | | | | | | | | | | | | | | | Bit means that there's an hardware problem with gyrometers
#  | | | | | | | | | | | | | | | | VBat low : (1) too low, (0) Ok
#  | | | | | | | | | | | | | | | VBat high (US mad) : (1) too high, (0) Ok
#  | | | | | | | | | | | | | | Timer elapsed : (1) elapsed, (0) not elapsed
#  | | | | | | | | | | | | | Power : (0) Ok, (1) not enough to fly
#  | | | | | | | | | | | | Angles : (0) Ok, (1) out of range
#  | | | | | | | | | | | Wind : (0) Ok, (1) too much to fly
#  | | | | | | | | | | Ultrasonic sensor : (0) Ok, (1) deaf
#  | | | | | | | | | Cutout system detection : (0) Not detected, (1) detected
#  | | | | | | | | PIC Version number OK : (0) a bad version number, (1) version number is OK
#  | | | | | | | ATCodec thread ON : (0) thread OFF (1) thread ON
#  | | | | | | Navdata thread ON : (0) thread OFF (1) thread ON
#  | | | | | Video thread ON : (0) thread OFF (1) thread ON
#  | | | | Acquisition thread ON : (0) thread OFF (1) thread ON
#  | | | CTRL watchdog : (1) delay in control execution (> 5ms), (0) control is well scheduled // Check frequency of control loop
#  | | ADC Watchdog : (1) delay in uart2 dsr (> 5ms), (0) uart2 is good // Check frequency of uart2 dsr (com with adc)
#  | Communication Watchdog : (1) com problem, (0) Com is ok // Check if we have an active connection with a client
#  Emergency landing : (0) no emergency, (1) emergency

ARDRONE_FLY_MASK            = 1 << 0  #/*!< FLY MASK : (0) ardrone is landed, (1) ardrone is flying */
ARDRONE_VIDEO_MASK          = 1 << 1  #/*!< VIDEO MASK : (0) video disable, (1) video enable */
ARDRONE_VISION_MASK         = 1 << 2  #/*!< VISION MASK : (0) vision disable, (1) vision enable */
ARDRONE_CONTROL_MASK        = 1 << 3  #/*!< CONTROL ALGO : (0) euler angles control, (1) angular speed control */
ARDRONE_ALTITUDE_MASK       = 1 << 4  #/*!< ALTITUDE CONTROL ALGO : (0) altitude control inactive (1) altitude control active */
ARDRONE_USER_FEEDBACK_START = 1 << 5  #/*!< USER feedback : Start button state */
ARDRONE_COMMAND_MASK        = 1 << 6  #/*!< Control command ACK : (0) None, (1) one received */
ARDRONE_FW_FILE_MASK        = 1 << 7  #/* Firmware file is good (1) */
ARDRONE_FW_VER_MASK         = 1 << 8  #/* Firmware update is newer (1) */
#//  ARDRONE_FW_UPD_MASK         = 1 << 9  /* Firmware update is ongoing (1) */
ARDRONE_NAVDATA_DEMO_MASK   = 1 << 10 #/*!< Navdata demo : (0) All navdata, (1) only navdata demo */
ARDRONE_NAVDATA_BOOTSTRAP   = 1 << 11 #/*!< Navdata bootstrap : (0) options sent in all or demo mode, (1) no navdata options sent */
ARDRONE_MOTORS_MASK  	      = 1 << 12 #/*!< Motors status : (0) Ok, (1) Motors problem */
ARDRONE_COM_LOST_MASK       = 1 << 13 #/*!< Communication Lost : (1) com problem, (0) Com is ok */
ARDRONE_VBAT_LOW            = 1 << 15 #/*!< VBat low : (1) too low, (0) Ok */
ARDRONE_USER_EL             = 1 << 16 #/*!< User Emergency Landing : (1) User EL is ON, (0) User EL is OFF*/
ARDRONE_TIMER_ELAPSED       = 1 << 17 #/*!< Timer elapsed : (1) elapsed, (0) not elapsed */
ARDRONE_ANGLES_OUT_OF_RANGE = 1 << 19 #/*!< Angles : (0) Ok, (1) out of range */
ARDRONE_ULTRASOUND_MASK     = 1 << 21 #/*!< Ultrasonic sensor : (0) Ok, (1) deaf */
ARDRONE_CUTOUT_MASK         = 1 << 22 #/*!< Cutout system detection : (0) Not detected, (1) detected */
ARDRONE_PIC_VERSION_MASK    = 1 << 23 #/*!< PIC Version number OK : (0) a bad version number, (1) version number is OK */
ARDRONE_ATCODEC_THREAD_ON   = 1 << 24 #/*!< ATCodec thread ON : (0) thread OFF (1) thread ON */
ARDRONE_NAVDATA_THREAD_ON   = 1 << 25 #/*!< Navdata thread ON : (0) thread OFF (1) thread ON */
ARDRONE_VIDEO_THREAD_ON     = 1 << 26 #/*!< Video thread ON : (0) thread OFF (1) thread ON */
ARDRONE_ACQ_THREAD_ON       = 1 << 27 #/*!< Acquisition thread ON : (0) thread OFF (1) thread ON */
ARDRONE_CTRL_WATCHDOG_MASK  = 1 << 28 #/*!< CTRL watchdog : (1) delay in control execution (> 5ms), (0) control is well scheduled */
ARDRONE_ADC_WATCHDOG_MASK   = 1 << 29 #/*!< ADC Watchdog : (1) delay in uart2 dsr (> 5ms), (0) uart2 is good */
ARDRONE_COM_WATCHDOG_MASK   = 1 << 30 #/*!< Communication Watchdog : (1) com problem, (0) Com is ok */
ARDRONE_EMERGENCY_MASK      = 1 << 31  #/*!< Emergency landing : (0) no emergency, (1) emergency */

def split(data):
  """Split a raw navdata packet received from the drone into a header and sequence of blocks.

  _data_ is a sequence of bytes received from the drone. Should this sequence
  of bytes be a valid navdata packet, this function returns a pair. The first
  element of the pair is the NavBlockHeader corresponding to the packet header.
  The second element is a sequence of block objects (e.g. DemoBlock).

  ''FIXME'' The error handling of this function is not all that it could be.

  """
  ndh = NavDataHeader.from_buffer_copy(data[0:ct.sizeof(NavDataHeader)])
  if not ndh.valid():
    log.error('Got invalid navdata packet')
    return (ndh, None)

  got_valid_checksum_option = False
  next_option_start = ct.sizeof(NavDataHeader)
  options = []

  while not got_valid_checksum_option and next_option_start < len(data):
    obh = OptionBlockHeader.from_buffer_copy(
        data[next_option_start:(next_option_start+ct.sizeof(OptionBlockHeader))])
    option_data = data[next_option_start:(next_option_start+obh.size)]
    this_option_start = next_option_start
    next_option_start += obh.size

    if obh.id == NAVDATA_CKS_TAG.value:
      cks = ChecksumBlock.from_buffer_copy(option_data)
      assert(cks.valid())
      options.append(cks)

      #got_cks = checksum(data[0:this_option_start])
      #if got_cks.value != cks.checksum:
      #  log.warning('navdata checksum mismatch: computed %s, got %s' % (got_cks, cks.checksum))
      #  return (ndh, [])
      got_valid_checksum_option = True
    elif obh.id == NAVDATA_DEMO_TAG.value:
      demo = DemoBlock.from_buffer_copy(option_data)
      assert(demo.valid())
      options.append(demo)
    elif obh.id == NAVDATA_VISION_DETECT_TAG.value:
      vd = VisionDetectBlock.from_buffer_copy(option_data)
      assert(vd.valid())
      options.append(vd)
    elif obh.id == NAVDATA_IPHONE_ANGLES_TAG.value:
      ipa = IPhoneAnglesBlock.from_buffer_copy(option_data)
      assert(ipa.valid())
      options.append(ipa)
    else:
      log.info('Unknown navdata option tag: %s' % (obh.id,))

  if not got_valid_checksum_option:
    log.error('Navdata packet did not have valid checksum.')
    return (ndh, [])

  return (ndh, options)

def checksum(data):
  """Compute a checksum for the passed data. data should be a sequence of bytes.

  Yes, this really is the checksum they're using(!)

  >>> checksum([ord(c) for c in 'hello']).value == 532
  True
  >>> checksum([ord(c) for c in "is is me you're looking for?"]).value == 2558
  True

  """
  checksum = ct.c_uint32(0)
  for d in data:
    checksum = ct.c_uint32(checksum.value + d)
  return checksum

class Matrix3x3(ct.LittleEndianStructure):
  """A 3x3 matrix (as expressed in navdata.c).

  >>> m = Matrix3x3()
  >>> ct.sizeof(m)
  36

  """
  _fields_ = [
      ('m11', ct.c_float),
      ('m12', ct.c_float),
      ('m13', ct.c_float),
      ('m21', ct.c_float),
      ('m22', ct.c_float),
      ('m23', ct.c_float),
      ('m31', ct.c_float),
      ('m32', ct.c_float),
      ('m33', ct.c_float),
  ]

class Vector3x1(ct.LittleEndianStructure):
  """A 3x1 matrix (as expressed in navdata.c).

  >>> v = Vector3x1()
  >>> ct.sizeof(v)
  12

  """
  _fields_ = [
      ('x', ct.c_float),
      ('y', ct.c_float),
      ('z', ct.c_float),
  ]

class NavDataHeader(ct.LittleEndianStructure):
  """The header of a navdata packet.

  >>> h = NavDataHeader()
  >>> ct.sizeof(h)
  16

  The header of this packet is invalid.

  >>> h.header
  0
  >>> h.valid()
  False

  Set it to be correct

  >>> h.header = 0x55667788
  >>> h.valid()
  True

  The header is an integer:

  >>> print(NavDataHeader.header)
  <Field type=c_int, ofs=0, size=4>

  """
  _fields_ = [
      ('header', ct.c_int32),
      ('state', ct.c_int32),
      ('sequence', ct.c_int32),
      ('vision_flag', ct.c_int32),
  ]

  def valid(self):
    if self.header != NAVDATA_HEADER.value:
      return False
    return True

class OptionBlockHeader(ct.LittleEndianStructure):
  """The header to an option block.

  >>> obh = OptionBlockHeader()
  >>> ct.sizeof(obh)
  4
  >>> print(OptionBlockHeader.size)
  <Field type=c_short, ofs=2, size=2>

  """
  _fields_ = [
      ('id', ct.c_int16),
      ('size', ct.c_int16),
  ]

class ChecksumBlock(ct.LittleEndianStructure):
  """A checksum block appended to the end of a navdata packet.

  >>> cs = ChecksumBlock()
  >>> ct.sizeof(cs)
  8
  >>> print(ChecksumBlock.checksum)
  <Field type=c_int, ofs=4, size=4>
  >>> cs.valid()
  False
  >>> cs.header.id = NAVDATA_CKS_TAG
  >>> cs.valid()
  True

  """
  _fields_ = [
      ('header', OptionBlockHeader),
      ('checksum', ct.c_int32),
  ]

  def json(self):
    return json.dumps({ 'checksum': self.checksum })

  def valid(self):
    return self.header.id == NAVDATA_CKS_TAG.value

class DemoBlock(ct.LittleEndianStructure):
  """A block of demo data. This has been lifted directly from the navdata.c
  file in the SDK since it is undocumented.

  Test basic creation:

  >>> db = DemoBlock()
  >>> ct.sizeof(db)
  44
  >>> db.header.id = 0xdeadbeef # rubbish
  >>> db.valid()
  False
  >>> db.header.id = NAVDATA_DEMO_TAG
  >>> db.valid()
  True

  """
  _fields_ = [
      ('header', OptionBlockHeader),
      ('ctrl_state', ct.c_uint32),              # instance of def_mykonos_state_mask_t (?)
      ('vbat_flying_percentage', ct.c_uint32),  # battery voltage filtered (mV)

      # attitude parameters
      ('theta', ct.c_float),
      ('phi', ct.c_float),
      ('psi', ct.c_float),

      ('altitude', ct.c_int32),                 # God knows what units(!)

      # estimates of linear velocity
      ('vx', ct.c_float),
      ('vy', ct.c_float),
      ('vz', ct.c_float),

      # index of the streamed (video?) frame
      ('num_frames', ct.c_uint32),

      ## camera parameters as computed by feature detection
      #('detection_camera_rot', Matrix3x3),
      #('detection_camera_homo', Matrix3x3),
      #('detection_camera_trans', Vector3x1),

      ## camera parameters as computed by the drone
      #('drone_camera_rot', Matrix3x3),
      #('drone_camera_trans', Vector3x1),
  ]

  def json(self):
    json_fields = [
        'ctrl_state', 'vbat_flying_percentage', 'theta', 'phi', 'psi',
        'altitude', 'vx', 'vy', 'vz', 'num_frames',
    ]
    json_dict = { }
    for field_name in json_fields:
      json_dict[field_name] = getattr(self, field_name)
    return json.dumps(json_dict)

  def valid(self):
    return self.header.id == NAVDATA_DEMO_TAG.value
  
class IPhoneAnglesBlock(ct.LittleEndianStructure):
  """A block of 'iPhone angles'. This has been lifted directly from the navdata.c
  file in the SDK since it is undocumented.

  Test basic creation:

  >>> ipab = IPhoneAnglesBlock()
  >>> ct.sizeof(ipab)
  24
  >>> ipab.valid()
  False
  >>> ipab.header.id = NAVDATA_IPHONE_ANGLES_TAG
  >>> ipab.valid()
  True

  """
  _fields_ = [
      ('header', OptionBlockHeader),
      ('enable', ct.c_int32),
      ('ax', ct.c_float),
      ('ay', ct.c_float),
      ('az', ct.c_float),
      ('elapsed', ct.c_uint32),
  ]

  def json(self):
    json_fields = [ 'enable', 'ax', 'ay', 'az', 'elapsed' ]
    json_dict = { }
    for field_name in json_fields:
      json_dict[field_name] = getattr(self, field_name)
    return json.dumps(json_dict)

  def valid(self):
    return self.header.id == NAVDATA_IPHONE_ANGLES_TAG.value
 
class VisionDetectBlock(ct.LittleEndianStructure):
  """A block of vision detector data. This has been lifted directly from the
  navdata.c file in the SDK since it is undocumented.

  Test basic creation:

  >>> vdb = VisionDetectBlock()
  >>> ct.sizeof(vdb)
  104
  >>> vdb.valid()
  False
  >>> vdb.header.id = NAVDATA_VISION_DETECT_TAG
  >>> vdb.valid()
  True

  """
  _fields_ = [
      ('header', OptionBlockHeader),
      ('nb_detected', ct.c_uint32),
      ('type', ct.c_uint32 * 4),
      ('xc', ct.c_uint32 * 4),
      ('yc', ct.c_uint32 * 4),
      ('width', ct.c_uint32 * 4),
      ('height', ct.c_uint32 * 4),
      ('dist', ct.c_uint32 * 4),
  ]

  def json(self):
    """This method returns a JSON object describing the dtected features but
    formats it in a different way: the dictionary has a single field,
    'features', which contains an array of features detected. Each feature has
    a 'xc', 'yc', 'width', 'height' and 'dist' field initialised from the packet.

    """
    features = []
    for idx in range(self.nb_detected):
      features.append({
        'xc': self.xc[idx], 'yc': self.yc[idx],
        'width': self.width[idx], 'height': self.height[idx],
        'dist': self.dist[idx]
      })
    return json.dumps({ 'features': features })

  def valid(self):
    return self.header.id == NAVDATA_VISION_DETECT_TAG.value

