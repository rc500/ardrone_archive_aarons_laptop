"""
Aruco Augemented Reality Library Support
========================================

This module wraps the C aruco library bindings which are also shipped with this
software. An example of using the module::

  import os
  import sys
  import numpy as np
  import ardrone.aruco as aruco
  import PIL

  # We load the input image into an array since we'll be modifying it by
  # drawing markers into it and PIL.Images, although they support the array
  # interface, are read-only.
  arr = np.array(PIL.Image.open('input.png').convert("RGB"))

  # Create a detector.
  detector = aruco.MarkerDetector()
  
  # Find the markers and draw them.
  markers = detector.detect(arr)
  for m in markers:
    m.draw(arr)

  # Write the output image.
  PIL.Image.fromarray(arr).save('output.png')

"""

import ctypes as ct
import numpy as np
from . import native

# Enums
_ARUCO_FAILURE = -1
_ARUCO_SUCCESS = 0

_ARUCO_FALSE = 0
_ARUCO_TRUE = 1

# Structures
class _Size(ct.Structure):
  _fields_ = [
      ('width', ct.c_int),
      ('height', ct.c_int),
  ]

class _Image(ct.Structure):
  _fields_ = [
      ('data', ct.POINTER(ct.c_uint8)),
      ('size', _Size),
  ]

# Basic types
def _Status(status):
  """A type wrapper callable that converts an aruco staus into an exception.
  
  """
  if status != _ARUCO_SUCCESS:
    raise ArucoError(
        _dll.aruco_error_last_str(),
        _dll.aruco_error_last_code())
  return status

_Handle = ct.POINTER(ct.c_int32)
_Size = ct.c_uint64
_ImagePtr = ct.POINTER(_Image)

# Load the DLL
_dll = native.load_dll('libcaruco')
if _dll is None:
  raise ImportError('Could not load caruco native library.')

# Function return and argument types
_dll.aruco_error_last_str.restype = ct.c_char_p

_dll.aruco_camera_parameters_new.restype = _Handle
_dll.aruco_camera_parameters_free.argtypes = ( _Handle, )
_dll.aruco_camera_parameters_is_valid.argtypes = ( _Handle, )
_dll.aruco_camera_parameters_save_to_file.restype = _Status
_dll.aruco_camera_parameters_save_to_file.argtypes = ( _Handle, ct.c_char_p )
_dll.aruco_camera_parameters_read_from_file.restype = _Status
_dll.aruco_camera_parameters_read_from_file.argtypes = ( _Handle, ct.c_char_p )
_dll.aruco_camera_parameters_read_from_xml_file.restype = _Status
_dll.aruco_camera_parameters_read_from_xml_file.argtypes = ( _Handle, ct.c_char_p )
_dll.aruco_camera_parameters_resize.argtypes = ( _Handle, ct.POINTER(_Size) )

_dll.aruco_marker_new.restype = _Handle
_dll.aruco_marker_free.argtypes = ( _Handle, )
_dll.aruco_marker_copy_from.argtypes = ( _Handle, _Handle )
_dll.aruco_marker_is_valid.argtypes = ( _Handle, )
_dll.aruco_marker_id.argtypes = ( _Handle, )
_dll.aruco_marker_calculate_extrinsics.restype = _Status
_dll.aruco_marker_calculate_extrinsics.argtypes = ( _Handle, ct.c_float, _Handle )
_dll.aruco_marker_draw.argtypes = (
    _Handle, _ImagePtr,
    ct.c_float, ct.c_float, ct.c_float, ct.c_int, ct.c_int
)

_dll.aruco_marker_detector_new.restype = _Handle
_dll.aruco_marker_detector_free.argtypes = ( _Handle, )
_dll.aruco_marker_detector_detect.restype = _Status
_dll.aruco_marker_detector_detect.argtypes = \
    ( _Handle, _ImagePtr, _Handle )

_dll.aruco_marker_vector_new.restype = _Handle
_dll.aruco_marker_vector_free.argtypes = ( _Handle, )
_dll.aruco_marker_vector_clear.argtypes = ( _Handle, )
_dll.aruco_marker_vector_size.argtypes = ( _Handle, )
_dll.aruco_marker_vector_element.restype = _Handle
_dll.aruco_marker_vector_element.argtypes = ( _Handle, _Size )

class ArucoError(Exception):
  """An exception which wraps an error returned from the aruco library.

  *msg* is a description of the error.

  *code* is an integer code for the error.

  """
  def __init__(self, msg, code=-1):
    self.code = code
    self.msg = msg

  def __str__(self):
    if self.code == -1:
      return str(self.msg)
    return "%s: %s" % (self.code, self.msg)

# Internal classes

class _HandleWrapper(object):
  """A wrapper around an aruco handle. Set the class attributes ``_new``,
  ``_free`` and (optionally) ``_copy`` in a derived class.

  """
  def __init__(self):
    assert _dll is not None
    self.handle = self.__class__._new()

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.close()

  def __del__(self):
    self.close()

  def copy_from(self, other_handle):
    if hasattr(self.__class__, '_copy'):
      self.__class__._copy(self.handle, other_handle)
    else:
      raise NotImplementedError('Copy not implemented')

  def close(self):
    if self.handle is None:
      return
    self.__class__._free(self.handle)
    self.handle = None

def _to_image(image):
  """Converts an object whcih exports the array interface to one which can be
  passed as an image pointer to a caruco API function.

  """
  arr = np.array(image, copy=False)

  # Check arraay type and shape
  if arr.ndim != 3 or arr.shape[2] != 3:
    raise ArucoError('Input image must have only 3 channels')
  if arr.dtype != np.uint8:
    raise ArucoError(
        'Input image must have 8-bit per channel colour depth. ' +
        'Data type is: ' + str(arr.dtype))

  # Create an image structure
  im = _Image()
  im.data = arr.ctypes.data_as(ct.POINTER(ct.c_uint8))
  im.size.width = arr.shape[0]
  im.size.height = arr.shape[1]
  return ct.byref(im)

class _MarkerVector(_HandleWrapper):
  _new = _dll.aruco_marker_vector_new
  _free = _dll.aruco_marker_vector_free

  def clear(self):
    _dll.aruco_marker_vector_clear(self.handle)

  def size(self):
    return _dll.aruco_marker_vector_size(self.handle)

  def contents(self):
    contents = []
    for idx in range(self.size()):
      m = Marker()
      m.copy_from(_dll.aruco_marker_vector_element(self.handle, idx))
      contents.append(m)
    return contents

# Public classes

class CameraParameters(_HandleWrapper):
  """Parameters of the camera.

  """
  _new = _dll.aruco_camera_parameters_new
  _free = _dll.aruco_camera_parameters_free
  _copy = _dll.aruco_camera_parameters_copy_from

  def is_valid(self):
    """Return True iff the parameters are valid."""
    return _dll.aruco_camera_parameters_is_valid(self.handle) == _ARUCO_TRUE

  def save_to_file(self, path):
    """Save the camera parameters to a file.
    
    *path* is a filesystem path
    
    Raises an ArucoError if there is a file I/O error.
    
    """
    _dll.aruco_camera_parameters_save_to_file(self.handle, path)

  def read_from_file(self, path):
    """Read the camera parameters from a file previously saved via
    save_to_file.
    
    *path* is a filesystem path
    
    Raises an ArucoError if there is a file I/O error.
    
    """
    _dll.aruco_camera_parameters_read_from_file(self.handle, path)

  def read_from_xml_file(self, path):
    """Read the camera parameters from an XML or YAML file as generated by
    OpenCV's calibration program.
    
    *path* is a filesystem path
    
    Raises an ArucoError if there is a file I/O error.
    
    """
    _dll.aruco_camera_parameters_read_from_xml_file(self.handle, path)

  def resize(self, size):
    """Adjust the parameters to the size of the image indicated.

    *size* is a pair specifying the width and height of the image in pixels.

    """
    sz = _Size()
    sz.width, sz.height = size
    _dll.aruco_camera_parameters_resize(self.handle, ct.byref(sz))

class Marker(_HandleWrapper):
  """This class represents a marker.
  """
  _new = _dll.aruco_marker_new
  _free = _dll.aruco_marker_free
  _copy = _dll.aruco_marker_copy_from

  def is_valid(self):
    """Return True iff the marker is valid."""
    return _dll.aruco_marker_is_valid(self.handle) == _ARUCO_TRUE

  def id(self):
    """Return an integer id for the marker."""
    return _dll.aruco_marker_id(self.handle)

  def draw(self, image,
      color = tuple((1.0, 0.0, 0.0)),
      line_width = 1, write_id = True):
    """Draw the marker into an image.

    *image* is an object which supports the array interface. It must be width x
    height x 3 in shape and have a datatype of ``u1`` (i.e. a byte).

    *color* is a red, green, blue triplet where each element is on the interfal
    [0,1].

    *line_width* is the width of the line used to draw the marker in the image.

    *write_id* is a flag indicating whether the integer marker id should be
    drawn into the image.

    """
    _dll.aruco_marker_draw(self.handle, _to_image(image),
        color[0], color[1], color[2], line_width,
        _ARUCO_TRUE if write_id else _ARUCO_FALSE)

class MarkerDetector(_HandleWrapper):
  """Main class for marker detection.

  """
  _new = _dll.aruco_marker_detector_new
  _free = _dll.aruco_marker_detector_free

  def detect(self, image, params=None, marker_size=None):
    """Detects the markers in the image passed.

    If you provide information about the camera parameters and the size of the
    marker, then, the extrinsics of the markers are detected.

    If one of *params* or *marker_size* is not None and the other is None, an
    ArucoError is raised.

    *params* is an instance of CameraParameters which must have been
    initialised to the camera intrinsics.

    *marker_size* is the size of the marker images in metres.

    Returns a sequence of Marker objects, one for each detected marker.

    """
    v = _MarkerVector()

    if (params is None) and (marker_size is None):
      _dll.aruco_marker_detector_detect(self.handle, _to_image(image), v.handle)
    elif (params is not None) and (marker_size is not None):
      _dll.aruco_marker_detector_detect_full(self.handle,
          _to_image(image), v.handle, params.handle, marker_size)
    else:
      raise ArucoError('Both params and marker_size must be None or ' +
          'both must not be None.')

    return v.contents()

def detect(image, params=None, marker_size=None):
  """Detects the markers in the image passed.

  This is a convenience wrapper around ``MarkerDetector.detect`` which creates
  an instance of the marker detector and then destructs it. This is useful for
  a one-off detection.

  See ``MarkerDetector.detect`` for full documentation.

  """
  with MarkerDetector() as d:
    return d.detect(image, params, marker_size)
