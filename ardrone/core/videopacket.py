"""
Parsing video packets
=====================

.. warning:: This module is a work in progress!

"""

import ctypes as ct
import os

import logging
log = logging.getLogger()

class Decoder(object):
  """A simple object which maintains a raw decoded image form of video packets sent to it.

  """
  def __init__(self, vid_cb = None):
    """Initialise the decoder.

    *vid_cb* is a callable which will be called with a sequence of bytes
    corresponding to the raw decoded video frame. If ``None``, no attempt is
    made to call it.

    """
    self.data = []
    self.vid_cb = vid_cb
    self._handle = None

    for basedir in ['dlls', os.path.join('..', '..', 'libp264', 'build')]:
      for dllfile in ['libp264', 'libp264.dll', 'libp264.so']:
        dllpath = os.path.join(os.path.dirname(__file__), basedir, dllfile)
        try:
          self._cdll = ct.CDLL(dllpath)
          self._handle = self._cdll.p264_open()
          log.info('Loaded video decoder library: %s' % (dllpath,))
          return
        except OSError as e:
          log.info('Failed to open video decoder library: %s' % (str(e),))
    log.error('Could not load any decoder library.')

  def decode(self, data):
    """Decode a raw video packet as received over the network from the drone.

    """
    if self._handle is None:
      return

    if 1 != self._cdll.p264_process_blockline(self._handle, data, len(data)):
      return

    get_image_buffer = self._cdll.p264_get_image_buffer
    get_image_buffer.restype = ct.POINTER(ct.c_char)
    self.data = get_image_buffer(self._handle)

    if self.vid_cb is not None:
      self.vid_cb(self.data[0:(320*240*2)])
