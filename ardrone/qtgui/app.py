"""Main application loop for the GUI program.

"""

import os
import sys

from PyQt4 import QtCore, QtGui, uic

from ..core.controlloop import ControlLoop
from ..platform import qt as platform

__resource_dir = os.path.dirname(__file__)

class MainWindow(QtGui.QMainWindow):
  def __init__(self, *args, **kwargs):
    QtGui.QMainWindow.__init__(self, *args, **kwargs)

    host, port = '192.168.1.1', 5556
    if 'DRONEDEBUG' in os.environ:
      host, port = '127.0.0.1', 5555
    
    connection = platform.Connection(drone_host=host, at_bind_port=port)
    self._control = ControlLoop(connection)
    self._control.connect()

  def takeOff(self):
    self._control.take_off()

  def land(self):
    self._control.land()

  def reset(self):
    self._control.reset()

  def hover(self):
    self._control.hover()

  def flatTrim(self):
    self._control.flat_trim()

def main():
	app = QtGui.QApplication(sys.argv)
	window = uic.loadUi(os.path.join(__resource_dir, 'main_window.ui'), MainWindow())
	window.show()
	sys.exit(app.exec_())
