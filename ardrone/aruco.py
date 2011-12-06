from . import native

import ctypes as ct
import numpy as np

# Enums
ARUCO_FAILURE = -1
ARUCO_SUCCESS = 0

ARUCO_FALSE = 0
ARUCO_TRUE = 1

_dll = native.load_dll('libcaruco')
if _dll is None:
  raise ImportError('Could not load caruco native library.')

# Function types

_dll.aruco_error_last_str.restype = ct.c_char_p

class ArucoError(Exception):
  def __init__(self, msg, code=-1):
    self.code = code
    self.msg = msg

  def __str__(self):
    if self.code == -1:
      return str(self.msg)
    return "%s: %s" % (self.code, self.msg)

def _last_error():
  return ArucoError(
      _dll.aruco_error_last_str(),
      _dll.aruco_error_last_code())

def _Status(status):
  if status != ARUCO_SUCCESS:
    raise _last_error()
  return status

_Handle = ct.POINTER(ct.c_int32)
_Size = ct.c_uint64
_ImagePtr = ct.POINTER(ct.c_uint8)

_dll.aruco_marker_new.restype = _Handle
_dll.aruco_marker_free.argtypes = ( _Handle, )
_dll.aruco_marker_copy_from.argtypes = ( _Handle, _Handle )
_dll.aruco_marker_is_valid.argtypes = ( _Handle, )
_dll.aruco_marker_id.argtypes = ( _Handle, )
_dll.aruco_marker_draw.argtypes = (
    _Handle, _ImagePtr, ct.c_uint32, ct.c_uint32,
    ct.c_float, ct.c_float, ct.c_float, ct.c_int, ct.c_int
)

_dll.aruco_marker_vector_new.restype = _Handle
_dll.aruco_marker_vector_free.argtypes = ( _Handle, )
_dll.aruco_marker_vector_clear.argtypes = ( _Handle, )
_dll.aruco_marker_vector_size.argtypes = ( _Handle, )
_dll.aruco_marker_vector_element.restype = _Handle
_dll.aruco_marker_vector_element.argtypes = ( _Handle, _Size )

_dll.aruco_marker_detector_new.restype = _Handle
_dll.aruco_marker_detector_free.argtypes = ( _Handle, )
_dll.aruco_marker_detector_detect.restype = _Status
_dll.aruco_marker_detector_detect.argtypes = \
    ( _Handle, _ImagePtr, ct.c_uint32, ct.c_uint32, _Handle )

class _HandleWrapper(object):
  def __init__(self):
    assert _dll is not None
    self.handle = self.__class__._new()

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.close()

  def __del__(self):
    self.close()

  def close(self):
    if self.handle is None:
      return
    self.__class__._free(self.handle)
    self.handle = None

def _image_data(image):
  arr = np.array(image, copy=False)
  if arr.ndim != 3 or arr.shape[2] != 3:
    raise ArucoError('Input image must have only 3 channels')
  if arr.dtype != np.uint8:
    raise ArucoError(
        'Input image must have 8-bit per channel colour depth. Data type is: %s' % (str(arr.dtype),))
  return (arr.ctypes.data_as(ct.POINTER(ct.c_uint8)), arr.shape[0], arr.shape[1])

class Marker(_HandleWrapper):
  _new = _dll.aruco_marker_new
  _free = _dll.aruco_marker_free

  def __init__(self, other_handle = None):
    super(Marker, self).__init__()
    if other_handle is not None:
      _dll.aruco_marker_copy_from(self.handle, other_handle)

  def is_valid(self):
    return _dll.aruco_marker_is_valid(self.handle) == ARUCO_TRUE

  def id(self):
    return _dll.aruco_marker_id(self.handle)

  def draw(self, image, color = tuple((1.0, 0.0, 0.0)), line_width = 1, write_id = True):
    data, w, h = _image_data(image)
    _dll.aruco_marker_draw(self.handle, data, w, h,
        color[0], color[1], color[2], line_width,
        ARUCO_TRUE if write_id else ARUCO_FALSE)

class MarkerVector(_HandleWrapper):
  _new = _dll.aruco_marker_vector_new
  _free = _dll.aruco_marker_vector_free

  def __init__(self):
    super(MarkerVector, self).__init__()

  def clear(self):
    _dll.aruco_marker_vector_clear(self.handle)

  def size(self):
    return _dll.aruco_marker_vector_size(self.handle)

  def contents(self):
    contents = []
    for idx in range(self.size()):
      h = _dll.aruco_marker_vector_element(self.handle, idx)
      contents.append(Marker(h))
    return contents

class MarkerDetector(_HandleWrapper):
  _new = _dll.aruco_marker_detector_new
  _free = _dll.aruco_marker_detector_free

  def __init__(self):
    super(MarkerDetector, self).__init__()

  def detect(self, image):
    v = MarkerVector()
    data, w, h = _image_data(image)
    _dll.aruco_marker_detector_detect(self.handle, data, w, h, v.handle)
    return v.contents()
