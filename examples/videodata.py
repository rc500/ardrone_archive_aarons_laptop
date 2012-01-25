import json
import os
import signal
import sys
import socket, time
import png
import numpy as np
from PIL import Image   
import zlib   

import logging
#logging.basicConfig(level=logging.DEBUG)


# This makes sure the path which python uses to find things when using import
# can find all our code.
sys.path.insert(0, os.path.abspath('..'))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
                                   
from ardrone.core import videopacket




# The magic runes required to import the Qt modules in a platform-independent
# way
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')
QtGui = qt.import_module('QtGui')


#specify image width and height
width=320
height=240


class ExampleApp(object):
  def __init__(self):

    # Create a Qt application loop. We use QCoreApplication because we're not
    # using any GUI features. If we were, we would use a QApplication.
    self.app = QtCore.QCoreApplication(sys.argv)

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

    #constructor for the decoder. Pass it a function that it calls after decoding as
    #an argument
    self._vid_decoder=videopacket.Decoder(self.frame)

    #constructor for png encoder: size of image to be encoded 320x240
    self.writer=png.Writer(width,height)


    
  def run(self):
    self.app.exec_()

  def heartbeat(self):
        pass

  #function called after image has been decoded. raw_video_frame is the decoded frame    
  def frame(self, raw_video_frame):
    print ('frame')
    #png.from_array(raw_video_frame)


    #code from stack overflow: convert from rgb565 to rgb888
    arr = np.fromstring(raw_video_frame,dtype=np.uint16).astype(np.uint32)
    arr = 0xFF000000 + ((arr & 0xF800) >> 8) + ((arr & 0x07E0) << 5) + ((arr & 0x001F) << 19)
    im1=Image.fromstring('RGBA', (width,height), arr, 'raw', 'RGBA', 0, 1)
    im1.save('frame2.jpg')


  def socketReadyRead(self):
    """Called when there is some interesting data to read on the control socket."""

    while self.socket.hasPendingDatagrams():
      sz = self.socket.pendingDatagramSize()
      (data, host, port) = self.socket.readDatagram(sz)

      # Some hack to account for PySide vs. PyQt differences
      if qt.USES_PYSIDE:
        data = data.data()

      #print ('Something interesting arrived')

      #decode the data
      self._vid_decoder.decode(data)
      
 

                  
if (__name__ == '__main__'):
  example_app = ExampleApp()
  example_app.run()
