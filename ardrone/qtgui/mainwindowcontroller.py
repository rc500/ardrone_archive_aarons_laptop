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

class MainWindowController(QtCore.QObject):
  """A class which takes care of connecting the GUI actions and widgets to the
  drone control loop.

  """
  def __init__(self, widget):
    super(QtCore.QObject, self).__init__()

    # Record the widget we're controlling.
    self._widget = widget

    # Find the log widget and wire in our custom log handler
    log_widget = self._widget.findChild(QtGui.QTextEdit, 'logTextEdit')
    if log_widget is not None:
      log_handler = TextEditLogHandler(log_widget)
      log_handler.setFormatter(logging.Formatter(
        fmt = '%(asctime)s:%(levelname)s:%(message)s',
        datefmt = '%Y/%d/%m:%H:%M:%S'
      ))
      log.addHandler(log_handler)
    else:
      log.error('Could not find log widget as child of widget passed to controller.')

    # Initialise the drone control loop and attempt to open a connection.
    log.info('Initialising control loop.')
    host, port = '192.168.1.1', 5556
    if 'DRONEDEBUG' in os.environ:
      host, port = '127.0.0.1', 5555
    connection = platform.Connection(drone_host=host, at_bind_port=port)
    self._control = ControlLoop(connection)
    self._control.connect()

    # Wire up our actions
    self._connect_action('actionFlatTrim', self.flat_trim)
    self._connect_action('actionTakeOff', self.take_off)
    self._connect_action('actionHover', self.hover)
    self._connect_action('actionReset', self.reset)
    self._connect_action('actionLand', self.land)

    # Set up a timer to try to detect the drone every 10 seconds
    self._detect_timer = QtCore.QTimer()
    self._detect_timer.setInterval(10000)
    self._detect_timer.timeout.connect(self._detectDrone)
    self._detect_timer.start()

    # Attempt to detect the drone for the first time
    self._detectDrone()

  def _detectDrone(self):
    manager = QtNetwork.QNetworkAccessManager(self)
    manager.finished[QtNetwork.QNetworkReply].connect(self.detectDroneReplyFinished)
    self._drone_request = manager.get(QtNetwork.QNetworkRequest(QtCore.QUrl('ftp://192.168.1.1/version.txt')))

  def _connect_action(self, name, cb):
    # Find the action.
    action = self._widget.findChild(QtGui.QAction, name)
    if action is None:
      log.error('Failed to find action "%s".' % (name,))
      return
    
    # Connect it.
    action.triggered.connect(cb)

  @qt.Slot()
  def detectDroneReplyFinished(self):
    log.debug('Drone detection via FTP returned: %s' % (str(self._drone_request.error()),))
    self._drone_detected = (self._drone_request.error() == QtNetwork.QNetworkReply.NoError)
    log.info('Drone present: %s' % (self._drone_detected,))

  @qt.Slot()
  def take_off(self):
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
  def flat_trim(self):
    log.info('Flat trim')
    self._control.flat_trim()


