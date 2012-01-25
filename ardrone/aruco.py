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

  # Find the markers and draw them.
  markers = aruco.detect_markers(arr)
  for m in markers:
    m.draw(arr)

  # Write the output image.
  PIL.Image.fromarray(arr).save('output.png')

"""

import ctypes as ct
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

_dll.aruco_board_new.restype = _Handle
_dll.aruco_board_free.argtypes = ( _Handle, )
_dll.aruco_board_draw_3d_axis.argtypes = ( _Handle, _ImagePtr, _Handle )
_dll.aruco_board_draw_3d_cube.argtypes = ( _Handle, _ImagePtr, _Handle )
_dll.aruco_board_get_extrinsics.argtypes = ( _Handle, ct.POINTER(ct.c_float), ct.POINTER(ct.c_float) )

_dll.aruco_board_configuration_new.restype = _Handle
_dll.aruco_board_configuration_free.argtypes = ( _Handle, )
_dll.aruco_board_configuration_save_to_file.restype = _Status
_dll.aruco_board_configuration_save_to_file.argtypes = ( _Handle, ct.c_char_p )
_dll.aruco_board_configuration_read_from_file.restype = _Status
_dll.aruco_board_configuration_read_from_file.argtypes = ( _Handle, ct.c_char_p )
_dll.aruco_board_configuration_marker_ids.argtypes = ( _Handle, ct.POINTER(ct.c_int) )

_dll.aruco_detect_board.restype = _Status
_dll.aruco_detect_board.argtypes = ( _Handle, _Handle, _Handle, _Handle, ct.c_float, ct.POINTER(ct.c_float) )

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
_dll.aruco_camera_parameters_get_camera_matrix.argtypes = ( _Handle, ct.POINTER(ct.c_float) )
_dll.aruco_camera_parameters_get_distortion_coeffs.argtypes = ( _Handle, ct.POINTER(ct.c_float) )

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
_dll.aruco_marker_centroid_x.argtypes = (_Handle, )
_dll.aruco_marker_centroid_y.argtypes = (_Handle, )
_dll.aruco_marker_draw_3d_axis.argtypes = ( _Handle, _ImagePtr, _Handle )
_dll.aruco_marker_draw_3d_cube.argtypes = ( _Handle, _ImagePtr, _Handle )

_dll.aruco_detect_markers.restype = _Status
_dll.aruco_detect_markers.argtypes = ( _ImagePtr, _Handle )
_dll.aruco_detect_markers_full.restype = _Status
_dll.aruco_detect_markers_full.argtypes = ( _ImagePtr, _Handle, _Handle, ct.c_float )

_dll.aruco_marker_vector_new.restype = _Handle
_dll.aruco_marker_vector_free.argtypes = ( _Handle, )
_dll.aruco_marker_vector_clear.argtypes = ( _Handle, )
_dll.aruco_marker_vector_size.argtypes = ( _Handle, )
_dll.aruco_marker_vector_element.restype = _Handle
_dll.aruco_marker_vector_element.argtypes = ( _Handle, _Size )
_dll.aruco_marker_vector_push_back.argtypes = ( _Handle, _Handle )

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

def _to_image(image, allow_read_only=True):
  """Converts an object whcih exports the array interface to one which can be
  passed as an image pointer to a caruco API function.

  The array interface is defined at
  http://docs.scipy.org/doc/numpy/reference/arrays.interface.html

  """
  # Check the input image supports the array interface
  if not hasattr(image, '__array_interface__'):
    raise ValueError('Input must support the array interface: ' +
        'http://docs.scipy.org/doc/numpy/reference/arrays.interface.html')

  array = image.__array_interface__
  if 'version' in array and array['version'] < 3:
    raise ValueError('Input must support >= version 3 of the array interface.')

  shape = array['shape']
  typestr = array['typestr']

  # Check array type and shape
  if len(shape) != 3 or shape[2] != 3:
    raise ValueError('Input must be an array with three colour channels, i.e. wxhx3 in shape.')
  if typestr != '|u1':
    raise ValueError('Input must be an array of bytes.')

  # Check packing
  if 'strides' in array and array['strides'] is not None:
    strides = array['strides']
    if strides != (shape[1]*shape[2],shape[2],1):
      raise ValueError('Input must be packed.')

  data_ptr = None

  # Do we have a data tuple?
  if 'data' in array and array['data'] is not None:
    data = array['data']
    if isinstance(data, tuple):
      # Check for read-only images
      if data[1] and not allow_read_only:
        raise ValueError('Input must not be read-only.')

      # Extract pointer
      data_ptr = ct.pointer(ct.c_uint8.from_address(data[0]))
    else:
      # data object must export buffer inteface.
      # An explicit check for string types.
      if isinstance(data, str):
        if not allow_read_only:
          raise ValueError('Input must not be read-only. Strings are read-only.')
        data_ptr = ct.cast(ct.c_char_p(data), ct.POINTER(ct.c_uint8))
      else:
        data_ptr = ct.pointer(ct.c_uint8.from_buffer(data))
  else:
    # If data entry is not present, use the buffer interface of the input
    data_ptr = ct.pointer(ct.c_uint8.from_buffer(image))

  assert data_ptr is not None

  # Create an image structure
  im = _Image()
  #im.data = np.array(image, copy=False).ctypes.data_as(ct.POINTER(ct.c_uint8))
  im.data = data_ptr
  im.size.width = shape[0]
  im.size.height = shape[1]
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
  
  def push_back(self, m):
    if not isinstance(m, Marker):
      raise ValueError('Expected instance of ardrone.aruco.Marker')
    _dll.aruco_marker_vector_push_back(self.handle, m.handle)

# Public classes

class Board(_HandleWrapper):
  """This class encapsulates the orientation and position of a detected board.

  """
  _new = _dll.aruco_board_new
  _free = _dll.aruco_board_free

  def draw_3d_axis(self, image, params):
    """Draw the 3d axis of this object into an image.

    *image* is an image to draw into (see Marker.draw for this object's type).

    *params* is an instance of CameraParameters.

    """
    _dll.aruco_board_draw_3d_axis(self.handle, _to_image(image, allow_read_only=False), params.handle)

  def draw_3d_cube(self, image, params):
    """Draw the 3d cube of this object into an image.

    *image* is an image to draw into (see Marker.draw for this object's type).

    *params* is an instance of CameraParameters.

    """
    _dll.aruco_board_draw_3d_cube(self.handle, _to_image(image, allow_read_only=False), params.handle)

  def get_extrinsics(self):
    """Return a pair describing the extrinsics of the board.
    
    The first element is a triple giving the Rodrigues rotation.
    
    The second element is a triple giving the translation vector for the board.

    """
    r = (ct.c_float * 3)()
    t = (ct.c_float * 3)()
    _dll.aruco_board_get_extrinsics(self.handle, r, t)

    return (tuple([float(x) for x in r]), tuple([float(x) for x in t]))

class BoardConfiguration(_HandleWrapper):
  """This class defines a board with several markers.

  """
  _new = _dll.aruco_board_configuration_new
  _free = _dll.aruco_board_configuration_free
  _copy = _dll.aruco_board_configuration_copy_from

  def save_to_file(self, path):
    """Save the board configuration to a file.
    
    *path* is a filesystem path
    
    Raises an ArucoError if there is a file I/O error.
    
    """
    _dll.aruco_board_configuration_save_to_file(self.handle, path)

  def read_from_file(self, path):
    """Read the board configuration from a file previously saved via
    save_to_file.
    
    *path* is a filesystem path
    
    Raises an ArucoError if there is a file I/O error.
    
    """
    _dll.aruco_board_configuration_read_from_file(self.handle, path)

  def marker_ids(self):
    """Return a sequence of integer marker ids for this board."""
    sz = _dll.aruco_board_configuration_marker_ids(self.handle, None)
    ids = (ct.c_int * sz)()
    _dll.aruco_board_configuration_marker_ids(self.handle, ids)
    return ids[:]

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

  def get_camera_matrix(self):
    m = (ct.c_float * 9)()
    _dll.aruco_camera_parameters_get_camera_matrix(self.handle, m)
    return ( 
        tuple([float(x) for x in m[0:3]]),
        tuple([float(x) for x in m[3:6]]),
        tuple([float(x) for x in m[6:9]]) )

  def get_distortion_coeffs(self):
    m = (ct.c_float * 4)()
    _dll.aruco_camera_parameters_get_distortion_coeffs(self.handle, m)
    return tuple([float(x) for x in m])

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

  def centroid_x(self):
	"""Return a cv::Point with location of centroid of marker"""
	return _dll.aruco_marker_centroid_x(self.handle)

  def centroid_y(self):
	"""Return a cv::Point with location of centroid of marker"""
	return _dll.aruco_marker_centroid_y(self.handle)
		
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
    _dll.aruco_marker_draw(self.handle, _to_image(image, allow_read_only=False),
        color[0], color[1], color[2], line_width,
        _ARUCO_TRUE if write_id else _ARUCO_FALSE)

  def draw_3d_axis(self, image, params):
    """Draw the 3d axis of this object into an image.

    *image* is an image to draw into (see Marker.draw for this object's type).

    *params* is an instance of CameraParameters.

    """
    _dll.aruco_marker_draw_3d_axis(self.handle, _to_image(image, allow_read_only=False), params.handle)

  def draw_3d_cube(self, image, params):
    """Draw the 3d cube of this object into an image.

    *image* is an image to draw into (see Marker.draw for this object's type).

    *params* is an instance of CameraParameters.

    """
    _dll.aruco_marker_draw_3d_cube(self.handle, _to_image(image, allow_read_only=False), params.handle)

def detect_board(markers, configuration, params, marker_size):
  """Detects a board given some markers.

  *markers* is a sequence of markers as returned from the MarkerDetector.

  *configuration* is a BoardConfiguration for the board.

  *params* is an instance of CameraParameters which must have been
  initialised to the camera intrinsics.

  *marker_size* is the size of the marker images in metres.

  Returns *board, lik*, an instance of the Board class describing the detected
  board and a float giving a measure of it's likelihood of being in the image.

  """

  mv = _MarkerVector()
  [mv.push_back(m) for m in markers]

  b = Board()
  lik = ct.c_float(0)
  _dll.aruco_detect_board(mv.handle, configuration.handle, b.handle, params.handle, marker_size, ct.byref(lik))
  return (b, lik.value)

def detect_markers(image, params=None, marker_size=None):
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
    _dll.aruco_detect_markers(_to_image(image), v.handle)
  elif (params is not None) and (marker_size is not None):
    _dll.aruco_detect_markers_full(_to_image(image), v.handle,
        params.handle, marker_size)
  else:
    raise ArucoError('Both params and marker_size must be None or ' +
        'both must not be None.')

  return v.contents()

