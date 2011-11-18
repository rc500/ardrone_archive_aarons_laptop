"""
Logging events to a UI widget
=============================

"""

import logging
import os
import time

from cgi import escape as html_escape
from ..util import qtcompat as qt

# Get a reference to an appropriate global logger.
log = logging.getLogger()

# Extract the various Qt modules we want to use
QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')

# Annoyingly PySide and PyQt4 have different ways of dealing with .ui files at
# runtime.
if qt.USES_PYSIDE:
  from PySide.QtUiTools import QUiLoader
else:
  from PyQt4 import uic

class LogView(QtGui.QTableView):
  """A view of log data represented in a LogModel.

  Use the setModel method to associate this view with the model.

  """
  def __init__(self, *args, **kwargs):
    super(LogView, self).__init__(*args, **kwargs)

    # Default style options for a log view
    self.horizontalHeader().setStretchLastSection(True)
    self.verticalHeader().hide()
    self.resizeColumnsToContents()

  def updateGeometries(self):
    super(LogView, self).updateGeometries()

    if self.model() is None:
      return

    # Resize all but the last column
    col_count = self.model().columnCount(QtCore.QModelIndex())
    row_count = self.model().rowCount(QtCore.QModelIndex())

    if col_count > 1:
      for col in range(col_count-1):
        self.resizeColumnToContents(col)
    
    if row_count > 0:
      self.scrollTo(self.model().index(row_count-1,0))

def _level_to_pixmap(level):
  """A class method which converts a log level to a QPixmap.

  >>> _level_to_pixmap(logging.DEBUG) == QtGui.QStyle.SP_MessageBoxInformation
  True
  >>> _level_to_pixmap(logging.INFO) == QtGui.QStyle.SP_MessageBoxInformation
  True
  >>> _level_to_pixmap(logging.WARNING) == QtGui.QStyle.SP_MessageBoxWarning
  True
  >>> _level_to_pixmap(logging.ERROR) == QtGui.QStyle.SP_MessageBoxCritical
  True
  >>> _level_to_pixmap(logging.CRITICAL) == QtGui.QStyle.SP_MessageBoxCritical
  True
  
  """
  icon = QtGui.QStyle.SP_MessageBoxInformation
  if level == logging.WARNING:
    icon = QtGui.QStyle.SP_MessageBoxWarning
  if level == logging.ERROR:
    icon = QtGui.QStyle.SP_MessageBoxCritical
  if level == logging.CRITICAL:
    icon = QtGui.QStyle.SP_MessageBoxCritical

  return QtGui.QApplication.style().standardIcon(icon)

class LogModel(QtCore.QAbstractTableModel, logging.Handler):
  """A simple logging.Handler sub-class which logs to a QTextEdit.

  """
  def __init__(self):
    logging.Handler.__init__(self)
    QtCore.QAbstractTableModel.__init__(self)

    # The actual records stored in a list
    self._records = []

    # A tuple giving a name and callables to extract the text and icon from the
    # record. If the callable is None, no corresponding information should be returned.
    self._columns = (
        ('', _level_to_pixmap, None),
        ('Time', None, lambda r: time.strftime('%H:%M:%S', time.localtime(r.created))),
        ('Message', None, lambda r: r.getMessage())
    )

  def headerData(self, section, orientation, role):
    if role != QtCore.Qt.DisplayRole:
      return None
    if orientation == QtCore.Qt.Horizontal:
      return self._columns[section][0]
    return str(section)

  def rowCount(self, parent):
    return len(self._records)

  def columnCount(self, parent):
    return len(self._columns)

  def data(self, index, role):
    row = index.row()
    col = index.column()

    if role == QtCore.Qt.DecorationRole:
      cb = self._columns[col][1]
    elif role == QtCore.Qt.DisplayRole:
      cb = self._columns[col][2]
    else:
      return None

    if cb is None:
      return None

    return cb(self._records[row])

  def emit(self, record):
    self.beginInsertRows(QtCore.QModelIndex(), len(self._records), len(self._records))
    self._records.append(record)
    self.endInsertRows()

def create_event_log_dock_widget():
  """Create and return a new event log QDockWidget.

  """
  # We should make use of the real resource manager for this(!)
  resource_dir = os.path.join(os.path.dirname(__file__), 'res')
  ui_file = os.path.join(resource_dir, 'dock_eventlog.ui')

  if qt.USES_PYSIDE:
    loader = QUiLoader()
    loader.registerCustomWidget(LogView)
    dock_widget = loader.load(ui_file)
  else:
    dock_widget = uic.loadUi(ui_file)
    
  # Find the log area and wire in our custom log handler
  log_view = dock_widget.findChild(LogView, 'logView')
  if log_view is not None:
    log_model = LogModel()
    log_view.setModel(log_model)
    log.addHandler(log_model)
  else:
    log.error('Could not find log widget as child of eventlog (looked for a LogView named logView).')

  return dock_widget
