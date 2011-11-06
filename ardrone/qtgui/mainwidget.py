import logging
import os

from ..util import qtcompat as qt
from cgi import escape as html_escape

# Import the actual drone control stuff.
from ..core.controlloop import ControlLoop
from ..platform import qt as platform

QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')
QtNetwork = qt.import_module('QtNetwork')

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

    # Set up a timer to try to detect the drone every 10 seconds
    self._detect_timer = QtCore.QTimer()
    self._detect_timer.setInterval(10000)
    self._detect_timer.timeout.connect(self.detectDrone)
    self._detect_timer.start()

    # Attempt to detect the drone for the first time
    self.detectDrone()

  def detectDrone(self):
    manager = QtNetwork.QNetworkAccessManager(self)
    manager.finished[QtNetwork.QNetworkReply].connect(self.detectDroneReplyFinished)
    manager.get(QtNetwork.QNetworkRequest(QtCore.QUrl('ftp://192.168.1.1/version.txt')))

  @qt.Slot()
  def detectDroneReplyFinished(self, p):
    log.debug('Drone detection via FTP returned: %s' % (str(p.error()),))
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


