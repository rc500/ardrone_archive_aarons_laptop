"""
Qt compatibility layer
======================

The ardrone system attempts to provide support both for the `PyQt
<http://www.riverbankcomputing.co.uk/software/pyqt/intro>`_ and `PySide
<http://www.pyside.org/>`_ bindings to Qt. This module provides a single
function which can be used to import a named Qt module.

"""

from __future__ import with_statement
from __future__ import division

_TRY_PYSIDE = True

try:
  if not _TRY_PYSIDE:
    raise ImportError()
  import PySide.QtCore as _QtCore
  QtCore = _QtCore
  USES_PYSIDE = True
except ImportError:
  import sip
  sip.setapi('QString', 2)
  sip.setapi('QVariant', 2)
  import PyQt4.QtCore as _QtCore
  QtCore = _QtCore
  USES_PYSIDE = False


def _pyside_import_module(moduleName):
  pyside = __import__('PySide', globals(), locals(), [moduleName], -1)
  return getattr(pyside, moduleName)


def _pyqt4_import_module(moduleName):
  pyside = __import__('PyQt4', globals(), locals(), [moduleName], -1)
  return getattr(pyside, moduleName)


if USES_PYSIDE:
  import_module = _pyside_import_module

  Signal = QtCore.Signal
  Slot = QtCore.Slot
  Property = QtCore.Property
else:
  import_module = _pyqt4_import_module

  Signal = QtCore.pyqtSignal
  Slot = QtCore.pyqtSlot
  Property = QtCore.pyqtProperty
