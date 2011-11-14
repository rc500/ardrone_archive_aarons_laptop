import logging, os
log = logging.getLogger()

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import numpy as np
from ..util import qtcompat as qt

# Extract the various Qt modules we want to use
QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')

# Annoyingly PySide and PyQt4 have different ways of dealing with .ui files at
# runtime.
if qt.USES_PYSIDE:
  from PySide.QtUiTools import QUiLoader
else:
  from PyQt4 import uic

class MatplotlibCanvas(FigureCanvas):
  """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
  def __init__(self, parent=None, width=5, height=4, dpi=100):
    fig = Figure(figsize=(width, height), dpi=dpi)
    super(MatplotlibCanvas, self).__init__(fig)
    self.setParent(parent)

    self.theta = self.figure.add_subplot(2,2,1)
    self.phi = self.figure.add_subplot(2,2,2)
    self.psi = self.figure.add_subplot(2,2,3)
    self.altitude = self.figure.add_subplot(2,2,4)

    self.theta.hold(False)
    self.phi.hold(False)
    self.psi.hold(False)
    self.altitude.hold(False)

    self.theta.set_title('theta')
    self.phi.set_title('phi')
    self.psi.set_title('psi')
    self.altitude.set_title('altitude')

    FigureCanvas.setSizePolicy(self,
                               QtGui.QSizePolicy.Expanding,
                               QtGui.QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)

class StatusDisplay(QtCore.QObject):
  def __init__(self, *args, **kwargs):
    super(StatusDisplay, self).__init__(*args, **kwargs)

    # We should make use of the real resource manager for this(!)
    resource_dir = os.path.join(os.path.dirname(__file__), 'res')
    ui_file = os.path.join(resource_dir, 'status_display.ui')

    self._thetas = np.array([], dtype=np.float32)
    self._psis = np.array([], dtype=np.float32)
    self._phis = np.array([], dtype=np.float32)
    self._altitudes = np.array([], dtype=np.float32)

    if qt.USES_PYSIDE:
      loader = QUiLoader()
      loader.registerCustomWidget(MatplotlibCanvas)
      self.widget = loader.load(ui_file)
    else:
      self.widget = uic.loadUi(ui_file)

    self._canvas = self.widget.findChild(MatplotlibCanvas, 'statusPlot')
    self._update_timer = None

  def new_pose(self, theta, psi, phi, altitude):
    self._thetas = np.append(self._thetas, theta)
    self._phis = np.append(self._phis, phi)
    self._psis = np.append(self._psis, psi)
    self._altitudes = np.append(self._altitudes, altitude)

    if self._update_timer is None:
      self._update_timer = True
      QtCore.QTimer.singleShot(2000, self._update)

  def _update(self):
    self._update_timer = None

    kw = { }
    
    self._canvas.theta.plot(self._thetas, **kw)
    self._canvas.psi.plot(self._psis, **kw)
    self._canvas.phi.plot(self._phis, **kw)
    self._canvas.altitude.plot(self._altitudes, **kw)

    self._canvas.theta.set_title('theta')
    self._canvas.phi.set_title('phi')
    self._canvas.psi.set_title('psi')
    self._canvas.altitude.set_title('altitude')

    self._canvas.draw()
