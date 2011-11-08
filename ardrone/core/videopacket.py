import ctypes as ct
import os

import logging
log = logging.getLogger()

class Decoder(object):
  """A simple object which maintains a raw decoded image form of video packets sent to it.

  """
  def __init__(self, vid_cb = None):
    self.data = []
    self.vid_cb = vid_cb
    self._handle = None

    dllpath = os.path.join(os.path.dirname(__file__), '..', '..', 'libp264', 'build', 'libp264.so')

    try:
      self._cdll = ct.CDLL(dllpath)
      self._handle = self._cdll.p264_open()
    except OSError as e:
      log.error('Failed to open video decoder library: %s' % (str(e),))

  def decode(self, data):
    if self._handle is None:
      return

    print('First byte: %s' % (data[0],))
    if 1 != self._cdll.p264_process_blockline(self._handle, data, len(data)):
      return

    get_image_buffer = self._cdll.p264_get_image_buffer
    get_image_buffer.restype = ct.c_char_p
    self.data = get_image_buffer(self._handle)

    #ba = QtCore.QByteArray.fromRawData(data[0:(320*240*2)])
    #print('First byte %s vs %s' % (ord(ba[0]),data[0]))
    #self.image = QtGui.QImage(ba, 320, 240, QtGui.QImage.Format_RGB16)
    #print('Got data %s' % (self.image,))
    if self.vid_cb is not None:
      self.vid_cb(data)
