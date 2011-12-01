"""
Parsing video packets
=====================

.. warning:: This module is a work in progress!

"""

from .. import native

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
    self._cdll = native.load_dll('libp264')
    if self._cdll is not None:
      # FIXME: The handle is never released. *BAD PROGRAMMER*
      self._handle = self._cdll.p264_open()
    else:
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
