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

import logging
from cgi import escape as html_escape

__resource_dir = os.path.dirname(__file__)

log = logging.getLogger()

class TextEditLogHandler(logging.Handler):
  def __init__(self, widget):
    logging.Handler.__init__(self)
    self._widget = widget

  def emit(self, record):
    te = self._widget.findChild(QtGui.QTextEdit, 'logTextEdit')
    if te is None:
      return
    msg = html_escape(self.format(record))
    te.insertHtml('<pre>' + msg + '<br></pre>')
    te.ensureCursorVisible()

class MainWidget(QtGui.QWidget):
  def __init__(self, *args, **kwargs):
    super(MainWidget, self).__init__(*args, **kwargs)

    host, port = '192.168.1.1', 5556
    if 'DRONEDEBUG' in os.environ:
      host, port = '127.0.0.1', 5555
    
    connection = platform.Connection(drone_host=host, at_bind_port=port)
    self._control = ControlLoop(connection)
    self._control.connect()

    self._log_handler = TextEditLogHandler(self)
    self._log_handler.setFormatter(logging.Formatter(
      fmt = '%(asctime)s:%(levelname)s:%(message)s',
      datefmt = '%Y-%d-%m:%H:%M:%S'
    ))
    log.addHandler(self._log_handler)

  @qt.Slot()
  def takeOff(self):
    log.info('Taking off')
    self._control.take_off()

  @qt.Slot()
  def land(self):
    log.info('Landing')
    self._control.land()

  @qt.Slot()
  def reset(self):
    log.info('Reset')
    self._control.reset()

  @qt.Slot()
  def hover(self):
    log.info('Hover')
    self._control.hover()

  @qt.Slot()
  def flatTrim(self):
    log.info('Flat trim')
    self._control.flat_trim()

def main():
  log.setLevel(logging.DEBUG)

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
