"""Main application loop for the GUI program.

"""

import os
import sys

try:
  from ..util import qtcompat as qt
except ImportError as e:
  raise ImportError('Qt appears not to be installed: %s' % (str(e),))

QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')

if qt.USES_PYSIDE:
  from PySide.QtUiTools import QUiLoader
else:
  from PyQt4 import uic

from ..core.controlloop import ControlLoop
from ..platform import qt as platform

__resource_dir = os.path.dirname(__file__)

class MainWidget(QtGui.QWidget):
  def __init__(self, *args, **kwargs):
    super(MainWidget, self).__init__(*args, **kwargs)

    host, port = '192.168.1.1', 5556
    if 'DRONEDEBUG' in os.environ:
      host, port = '127.0.0.1', 5555
    
    connection = platform.Connection(drone_host=host, at_bind_port=port)
    self._control = ControlLoop(connection)
    self._control.connect()

  @qt.Slot()
  def takeOff(self):
    self._control.take_off()

  @qt.Slot()
  def land(self):
    self._control.land()

  @qt.Slot()
  def reset(self):
    self._control.reset()

  @qt.Slot()
  def hover(self):
    self._control.hover()

  @qt.Slot()
  def flatTrim(self):
    self._control.flat_trim()

def main():
  app = QtGui.QApplication(sys.argv)
  ui_file = os.path.join(__resource_dir, 'main_window.ui')

  if qt.USES_PYSIDE:
    loader = QUiLoader()
    loader.registerCustomWidget(MainWidget)
    window = loader.load(ui_file)
  else:
    window = uic.loadUi(ui_file)
  
  window.show()
  sys.exit(app.exec_())
