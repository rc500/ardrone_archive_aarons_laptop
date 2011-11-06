"""Main application loop for the GUI program.

"""

import os
import sys

# We support both the PyQt4 (prevalent on Linux) and PySide (OS X) bindings for
# Qt. The qtcompat module provides the various shenanigans that are required to
# load one or the other. In this case if neight Qt bindings could be loaded,
# present a friendly error.
try:
  from ..util import qtcompat as qt
except ImportError as e:
  raise ImportError('Qt appears not to be installed: %s' % (str(e),))

# Extract the various Qt modules we want to use
QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')
QtNetwork = qt.import_module('QtNetwork')

# Annoyingly PySide and PyQt4 have different ways of dealing with .ui files at
# runtime.
if qt.USES_PYSIDE:
  from PySide.QtUiTools import QUiLoader
else:
  from PyQt4 import uic

# Import the actual drone control stuff.
from ..core.controlloop import ControlLoop
from ..platform import qt as platform

# Support for logging.
import logging
from cgi import escape as html_escape

# Should make use of the real resource manager for this(!)
__resource_dir = os.path.dirname(__file__)

log = logging.getLogger()

class TextEditLogHandler(logging.Handler):
  """A simple logging.Handler sub-class which logs to a QTextEdit.

  """
  def __init__(self, widget):
    logging.Handler.__init__(self)
    self._widget = widget

  def emit(self, record):
    if self._widget is None:
      return
    msg = html_escape(self.format(record))
    self._widget.insertHtml('<pre>' + msg + '<br></pre>')
    self._widget.ensureCursorVisible()

class MainWidget(QtGui.QWidget):
  def __init__(self, *args, **kwargs):
    super(MainWidget, self).__init__(*args, **kwargs)

  def postUiInit(self):
    self._log_widget = self.findChild(QtGui.QTextEdit, 'logTextEdit')
    self._log_handler = TextEditLogHandler(self._log_widget)
    self._log_handler.setFormatter(logging.Formatter(
      fmt = '%(asctime)s:%(levelname)s:%(message)s',
      datefmt = '%Y/%d/%m:%H:%M:%S'
    ))
    log.addHandler(self._log_handler)

    host, port = '192.168.1.1', 5556
    if 'DRONEDEBUG' in os.environ:
      host, port = '127.0.0.1', 5555
    
    log.info('Initialising control loop.')
    connection = platform.Connection(drone_host=host, at_bind_port=port)
    self._control = ControlLoop(connection)
    self._control.connect()

    self.detectDrone()

  def detectDrone(self):
    manager = QtNetwork.QNetworkAccessManager(self)
    manager.finished[QtNetwork.QNetworkReply].connect(self.detectDroneReplyFinished)
    manager.get(QtNetwork.QNetworkRequest(QtCore.QUrl('ftp://192.168.1.1/version.txt')))

  @qt.Slot()
  def detectDroneReplyFinished(self, p):
    log.info('Drone detection via FTP returned: %s' % (str(p.error()),))
    self._drone_detected = (p.error() == QtNetwork.QNetworkReply.NoError)
    log.info('Drone present: %s' % (self._drone_detected,))

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

def load_ui():
  """This function performs the required magic to load the .ui file for the
  main window using the appropriate method in PySide and PyQt4. After loading,
  we also call the postUiInit() method on the MainWidget so that further setup
  can take place there.

  """
  ui_file = os.path.join(__resource_dir, 'main_window.ui')

  if qt.USES_PYSIDE:
    loader = QUiLoader()
    loader.registerCustomWidget(MainWidget)
    window = loader.load(ui_file)
  else:
    window = uic.loadUi(ui_file)

  window.findChild(MainWidget, 'mainWidget').postUiInit()

  return window

def main():
  """The main entry point for the application. Call this from your script to
  launch the application. This function eventually calls QApplication.exec_()
  so don't expect it to return until the application should exit.

  """
  log.setLevel(logging.DEBUG)

  # Create the main application
  app = QtGui.QApplication(sys.argv)

  # Load and show the QMainWindow for this application.
  # (NB: we need to keep it in the symbol table so that the widget doesn't get
  # garbage collected under us. Don't you love Python!)
  main_window = load_ui()
  main_window.show()
  
  # Enter the application main loop
  sys.exit(app.exec_())
