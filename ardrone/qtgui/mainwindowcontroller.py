"""
The main GUI window
===================

"""

import logging
import os
import json

from ..util import qtcompat as qt
from cgi import escape as html_escape

# Import the actual drone control stuff.
from ..core.controlloop import ControlLoop
from ..core import navdata
from ..platform import qt as platform

# Utility widgets
from .dronedetection import *
from .eventlog import create_event_log_dock_widget
#from .statusdisplay import StatusDisplay

QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')

log = logging.getLogger()

class MainWindowController(QtCore.QObject):
  """A class which takes care of connecting the GUI actions and widgets to the
  drone control loop.

  """

  def _get_bat(self):
    return self._drone_battery_percentage

  def _set_bat(self, p):
    self._drone_battery_percentage = p
    self.batteryPercentageChanged.emit(p)

  """A property giving the last known battery percentage of the drone."""
  batteryPercentage = qt.Property(int, _get_bat, _set_bat)

  batteryPercentageChanged = qt.Signal(int)

  def __init__(self, widget):
    super(MainWindowController, self).__init__()

    self.batteryPercentage = 0;

    # Record the widget we're controlling.
    self._widget = widget

    log_dock = create_event_log_dock_widget()
    self._widget.addDockWidget(QtCore.Qt.BottomDockWidgetArea, log_dock)

    # Initialise the drone control loop and attempt to open a connection.
    log.info('Initialising control loop.')
    connection = platform.Connection()
    self._control = ControlLoop(connection, video_cb=self._vid_cb, navdata_cb=self._navdata_cb)

    # Create a drone connection statusbar widget
    status_bar = self._widget.statusBar()
    if status_bar is not None:
      self._drone_detect_label = DroneDetectionStateLabel()
      status_bar.addPermanentWidget(self._drone_detect_label)

      # Set up drone detection.
      self._drone_detector = DroneDetector()

      # Wire the drone detector into the label
      self._drone_detector.droneDetectionStateChanged.connect(self._drone_detect_label.setState)
      self._drone_detect_label.setState(self._drone_detector.droneDetectionState)

      # Battery label
      bat_label = QtGui.QLabel()
      status_bar.addPermanentWidget(bat_label)
      self.batteryPercentageChanged.connect(lambda x: bat_label.setText('Bat: ' + str(x) + '%'))
    else:
      log.error('No status bar found on QMainWindow.')

    self._cam_label = self._widget.findChild(QtGui.QLabel, 'camLabel')
    if self._cam_label is not None:
      self._cam_label.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(320,240,QtGui.QImage.Format_RGB16)))
    else:
      log.error('No camera label found on QMainWindow.')

    # Wire up our actions
    self._connect_action('actionFlatTrim', self.flat_trim)
    self._connect_action('actionTakeOff', self.take_off)
    self._connect_action('actionHover', self.hover)
    self._connect_action('actionReset', self.reset)
    self._connect_action('actionLand', self.land)
    self._connect_action('actionStartVideo', self.start_video)
    self._connect_action('actionStartNavdata', self.start_navdata)

    #self._status_display = StatusDisplay()
    #self._widget.centralWidget().layout().addWidget(self._status_display.widget)
    #for i in range(40):
    #  self._status_display.new_pose(1,2,3,4)
    #  self._status_display.new_pose(4,3,2,1)

  def _connect_action(self, name, cb):
    # Find the action.
    action = self._widget.findChild(QtGui.QAction, name)
    if action is None:
      log.error('Failed to find action "%s".' % (name,))
      return
    
    # Connect it.
    action.triggered.connect(cb)

  def _vid_cb(self, data):
    """Update the image in the camera window."""
    self._cam_label.setPixmap(QtGui.QPixmap(QtGui.QImage(data, 320, 240, QtGui.QImage.Format_RGB16)))

  def _navdata_cb(self, block):
    if isinstance(block, navdata.DemoBlock):
      self.batteryPercentage = block.vbat_flying_percentage
      #self._status_display.new_pose(block.theta, block.psi, block.phi, block.altitude)
    elif isinstance(block, navdata.VisionDetectBlock):
      # Parse the features from the block
      features = json.loads(block.json())['features']
    elif isinstance(block, navdata.ChecksumBlock):
      # This is handled by the control loop, we'll just ignore this
      pass
    else:
      log.debug('Got unhandled navdata block: %s' % (block.json(),))

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
    self._control.bootstrap()

  @qt.Slot()
  def hover(self):
    log.info('Hover')
    self._control.hover()

  @qt.Slot()
  def flat_trim(self):
    log.info('Flat trim')
    self._control.flat_trim()

  def _video_cb(self, im):
    print('Image: %s' % (str(im),))
    self._cam_label.setPixmap(QtGui.QPixmap.fromImage(im))

  @qt.Slot()
  def start_video(self):
    log.info('Start video')
    self._control.start_video()

  @qt.Slot()
  def start_navdata(self):
    log.info('Start navdata')
    self._control.start_navdata()


