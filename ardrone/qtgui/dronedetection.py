"""
Detecting the drone
===================

"""
import logging

from ..util import qtcompat as qt

QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')
QtNetwork = qt.import_module('QtNetwork')

log = logging.getLogger()

class DroneDetector(QtCore.QObject):
  """An object which polls the drone and fixed intervals to see if it can be detected."""

  """Successfully getting this URL counts as detecting the drone."""
  __detect_url = QtCore.QUrl('ftp://192.168.1.1/licenses.txt')

  def _get_drone_detected(self):
    return self._drone_detected

  def _set_drone_detected(self, flag):
    if not hasattr(self, '_drone_detected') or flag != self._drone_detected: 
      self._drone_detected = flag
      self.droneDetectionStateChanged.emit(self._drone_detected)

  """A property used to reflect the current drone detection state."""
  droneDetectionState = qt.Property(bool, _get_drone_detected, _set_drone_detected)

  """A signal emitted when the drone detection state *changes*. The new state is passed."""
  droneDetectionStateChanged = qt.Signal(bool)

  def __init__(self, poll_interval=5000):
    super(DroneDetector, self).__init__()

    # Initially no drone is detected
    self.droneDetectionState = False

    # Set up a timer to try to detect the drone every 10 seconds
    self._detect_timer = QtCore.QTimer()
    self._detect_timer.setInterval(poll_interval)
    self._detect_timer.timeout.connect(self._detectDrone)
    self._detect_timer.start()

    # Attempt to detect the drone for the first time
    self._detectDrone()

  def _detectDrone(self):
    manager = QtNetwork.QNetworkAccessManager(self)
    manager.finished[QtNetwork.QNetworkReply].connect(self.detectDroneReplyFinished)
    log.debug('Detecting drone by attempting to fetch: %s' % (DroneDetector.__detect_url.toString(),))
    self._drone_request = manager.get(QtNetwork.QNetworkRequest(QtCore.QUrl(DroneDetector.__detect_url)))

  @qt.Slot()
  def detectDroneReplyFinished(self):
    log.debug('Drone detection returned: %s' % (str(self._drone_request.error()),))
    self.droneDetectionState = (self._drone_request.error() == QtNetwork.QNetworkReply.NoError)
    log.debug('Drone present: %s' % (self._drone_detected,))

class DroneDetectionStateLabel(QtGui.QLabel):
  def __init__(self, initial_state = False, *args, **kwargs):
    super(DroneDetectionStateLabel, self).__init__(*args, **kwargs)
    self.setState(initial_state)

  @qt.Slot(bool)
  def setState(self, state):
    if state:
      self.setText('<span style="color: green">Drone found</span>')
    else:
      self.setText('<span style="color: red">Drone not found</span>')

