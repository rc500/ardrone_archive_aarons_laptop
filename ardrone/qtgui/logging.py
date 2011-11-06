import logging
import time

from ..util import qtcompat as qt
from cgi import escape as html_escape

QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')

log = logging.getLogger()

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

    # Resize all but the last column
    if self.model() is not None:
      col_count = self.model().columnCount(QtCore.QModelIndex())
      if col_count > 1:
        for col in range(col_count-1):
          self.resizeColumnToContents(col)


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
        ('', LogModel._level_to_pixmap, None),
        ('Time', None, lambda r: time.strftime('%H:%M:%S', time.localtime(r.created))),
        ('Message', None, lambda r: r.getMessage())
    )

  def _level_to_pixmap(level):
    """A class method which converts a log level to a QPixmap.

    >>> LogModel._level_to_pixmap(logging.DEBUG) == QtGui.QStyle.SP_MessageBoxInformation
    True
    >>> LogModel._level_to_pixmap(logging.INFO) == QtGui.QStyle.SP_MessageBoxInformation
    True
    >>> LogModel._level_to_pixmap(logging.WARNING) == QtGui.QStyle.SP_MessageBoxWarning
    True
    >>> LogModel._level_to_pixmap(logging.ERROR) == QtGui.QStyle.SP_MessageBoxCritical
    True
    >>> LogModel._level_to_pixmap(logging.CRITICAL) == QtGui.QStyle.SP_MessageBoxCritical
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
