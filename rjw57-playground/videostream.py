import json
import os
import signal
import sys
import socket
import time
import threading
import Queue

import cv2.cv as cv
import numpy as np

#from . import videopacket
#self._vid_decoder = videopacket.Decoder()

# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# The magic runes required to import the Qt modules in a platform-independent
# way
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')
QtNetwork = qt.import_module('QtNetwork')

from ardrone.core.videopacket import Decoder

# Load the tracker module
from tracker import Tracker

class TrackerThread(threading.Thread):
  def __init__(self, bc_file, cp_file):
    super(TrackerThread, self).__init__()
    self._tracker = Tracker(bc_file, cp_file)
    self._queue = Queue.Queue(maxsize=2)
    self._recon_images = []

  def run(self):
    while True:
      im = self._queue.get()
      self._tracker.new_image(im)
      self._recon_images = [self._tracker.recon_image(i) for i in range(len(self._tracker.boards))]

  def put_image(self, im):
    try:
      self._queue.put(im, block=False)
    except Queue.Full:
      pass

  def recon_images(self):
    return self._recon_images

  def recon_image(self, idx):
    return self._recon_images[idx]

class ExampleApp(object):
  def __init__(self):
    # Check the command-line arcuments.
    if len(sys.argv) < 3:
      print('usage: videostream.py camera_params.yml [board_config.abc...]')
      sys.exit(1)

    # Create the tracker
    self._tracker = TrackerThread(sys.argv[1], sys.argv[2:])
    self._tracker.daemon = True
    self._tracker.start()

    # Create a Qt application loop. We use QCoreApplication because we're not
    # using any GUI features. If we were, we would use a QApplication.
    self.app = QtGui.QApplication(sys.argv)

    # A video decoder object, wiring up video_frame_decoded to be called when a new
    # video frame is available.
    self._decoder = Decoder(self.video_frame_decoded)

    # This wires up Ctrl-C to call QApplication.quit()
    signal.signal(signal.SIGINT, lambda *args: self.app.quit())
 
    # Create a little 'heartbeat' timer that will call heartbeat() every so often.
    self.heartbeat_timer = QtCore.QTimer()
    self.heartbeat_timer.setInterval(50) # ms
    self.heartbeat_timer.timeout.connect(self.heartbeat)
    self.heartbeat_timer.start()

    # Set up a UDP listening socket on port 5562.
    self.socket = QtNetwork.QUdpSocket()
    if not self.socket.bind(QtNetwork.QHostAddress.Any, 5562):
      raise RuntimeError('Error binding to port: %s' % (self.socket.errorString()))
    self.socket.readyRead.connect(self.socketReadyRead)

    # the input raw video is a 2-byte per pixel image encoded as a RGB565 format.
    self._raw_image_mat = cv.CreateMatHeader(240, 320, cv.CV_8UC2)

    # we convert the image to this 3-byte per pixel RGB888 format
    self._image = cv.CreateMat(240, 320, cv.CV_8UC3)

    #self._video_win = QtGui.QWidget()
    #layout = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom, self._video_win)
    self._win = QtGui.QWidget()
    grid = QtGui.QGridLayout(self._win)

    self._detect_image_labels = []
    idx = 0
    for b in self._tracker._tracker.boards:
      col = int(idx % 3)
      row = int(idx / 3)
      idx += 1

      detect_image_label = QtGui.QLabel()
      grid.addWidget(detect_image_label, row, col)
      self._detect_image_labels.append(detect_image_label)

    col = int(idx % 3)
    row = int(idx / 3)
    idx += 1
    
    self._input_image_label = QtGui.QLabel()
    self._input_image_label.setPixmap(QtGui.QPixmap(QtGui.QImage(320, 240, QtGui.QImage.Format_RGB16)))
    grid.addWidget(self._input_image_label, row, col)
    #layout.addWidget(self._input_image_label)

    self._win.show()
    #self._video_win.show()
    
    self._update_timer = QtCore.QTimer()
    self._update_timer.setInterval(1000/15)
    self._update_timer.timeout.connect(self.update_images)
    self._update_timer.start()

  def run(self):
    self.app.exec_()

  def heartbeat(self):
        pass

  def socketReadyRead(self):
    """Called when there is some interesting data to read on the control socket."""

    while self.socket.hasPendingDatagrams():
      sz = self.socket.pendingDatagramSize()
      (data, host, port) = self.socket.readDatagram(sz)

      # Some hack to account for PySide vs. PyQt differences
      if qt.USES_PYSIDE:
        data = data.data()
  
      # Parse the packet
      self._decoder.decode(data)

  def video_frame_decoded(self, frame):
    """Called by the video decoded when a frame has been decoded.

    *frame* is a sequence of 320*240*2 = 153600 bytes which represent the video
    frame in RGB565 format.

    """

    # Set the data for the raw image data matrix
    cv.SetData(self._raw_image_mat, frame)

    # Colour convert. We can only colour convert in opencv from BGR565, not
    # RGB565. Luckily, the two wrongs average out to a right if we treat this
    # image as BGR from now on.
    cv.CvtColor(self._raw_image_mat, self._image, cv.CV_BGR5652RGB)

    self._tracker.put_image(self._image)

  def update_images(self):
    # Update the label images
    idx = 0
    for im in self._tracker.recon_images():
      try:
        label = self._detect_image_labels[idx]
        idx += 1

        if im is not None:
          label.setPixmap(QtGui.QPixmap(QtGui.QImage(
            im, im.shape[1], im.shape[0], QtGui.QImage.Format_RGB888)))
      except IndexError:
        pass

    # Update the label image
    self._input_image_label.setPixmap(QtGui.QPixmap(QtGui.QImage(
      self._image.tostring(), 320, 240, QtGui.QImage.Format_RGB888)))

if (__name__ == '__main__'):
  example_app = ExampleApp()
  example_app.run()
