"""ctype structures for navdata.

"""

import ctypes as ct

"""The header for a navdata packet."""
NAVDATA_HEADER = ct.c_int32(0x55667788)

"""The navdata demo tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_DEMO_TAG = ct.c_int16(0)

"""The navdata vision detect tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_VISION_DETECT_TAG = ct.c_int16(16)

"""The navdata 'iPhone angles' tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_IPHONE_ANGLES_TAG = ct.c_int16(18)

"""The navdata checksum tag for an option packet. (Lifted from navdata.c)"""
NAVDATA_CKS_TAG = ct.c_int16(0xffff)

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

  def valid(self):
    return self.header.id == NAVDATA_CKS_TAG.value

class DemoBlock(ct.LittleEndianStructure):
  """A block of demo data. This has been lifted directly from the navdata.c
  file in the SDK since it is undocumented.

  Test basic creation:

  >>> db = DemoBlock()
  >>> ct.sizeof(db)
  176
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

      # camera parameters as computed by feature detection
      ('detection_camera_rot', Matrix3x3),
      ('detection_camera_homo', Matrix3x3),
      ('detection_camera_trans', Vector3x1),

      # camera parameters as computed by the drone
      ('drone_camera_rot', Matrix3x3),
      ('drone_camera_trans', Vector3x1),
  ]

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

  def valid(self):
    return self.header.id == NAVDATA_VISION_DETECT_TAG.value

