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
QtGui = qt.import_module('QtGui')

# Annoyingly PySide and PyQt4 have different ways of dealing with .ui files at
# runtime.
if qt.USES_PYSIDE:
  from PySide.QtUiTools import QUiLoader
else:
  from PyQt4 import uic

# Support for logging.
import logging

from .mainwidget import MainWidget

# Should make use of the real resource manager for this(!)
__resource_dir = os.path.dirname(__file__)

log = logging.getLogger()

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
