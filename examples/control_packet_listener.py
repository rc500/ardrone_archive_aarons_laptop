"""
Listening for control packets from the drone
============================================

This example is a simple Python example which sets up a Qt event loop which
listens for a control packet from the drone controller and displays it when
received.

"""

import json
import os
import signal
import sys

# This makes soure the path which python uses to find things when using import
# can find all our code.
this_file_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(this_file_dir, '..')))

# The magic runes required to import the Qt modules in a platform-independent
# way
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')

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

    # Set up a UDP listening socket on port 5561.
    self.socket = QtNetwork.QUdpSocket()
    if not self.socket.bind(QtNetwork.QHostAddress.Any, 5561):
      raise RuntimeError('Error binding to port: %s' % (self.socket.errorString()))
    self.socket.readyRead.connect(self.socketReadyRead)

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
      packet = json.loads(data.decode())

      # Print it prettily
      print(json.dumps(packet, indent=True))

if __name__ == '__main__':
  example_app = ExampleApp()
  example_app.run()
