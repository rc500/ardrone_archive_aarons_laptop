"""Main application loop for the GUI program.

"""

import logging
import os
import sys

# Get a reference to an appropriate global logger.
log = logging.getLogger()

# We support both the PyQt4 (prevalent on Linux) and PySide (OS X) bindings for
# Qt. The qtcompat module provides the various shenanigans that are required to
# load one or the other. In this case if neither Qt bindings could be loaded,
# present a friendly error.
try:
  from ..util import qtcompat as qt
except ImportError as e:
  raise ImportError('Qt appears not to be installed: %s' % (str(e),))

# Extract the various Qt modules we want to use
QtCore = qt.import_module('QtCore')
QtGui = qt.import_module('QtGui')

# Annoyingly PySide and PyQt4 have different ways of dealing with .ui files at
# runtime.
if qt.USES_PYSIDE:
  from PySide.QtUiTools import QUiLoader
else:
  from PyQt4 import uic

from .mainwindowcontroller import MainWindowController

class Application(QtGui.QApplication):
  """A sub-class of QApplication which loads the main .ui file and creates a
  controller for it.

  Create an application:

  >>> a = Application()
  
  Add a timer so that it will exit after a second.
  
  >>> QtCore.QTimer.singleShot(1000, a.quit)

  Run it.

  >>> a.exec_()
  0

  """
  # Should make use of the real resource manager for this(!)
  __resource_dir = os.path.join(os.path.dirname(__file__), 'res')

  def __init__(self):
    super(Application, self).__init__(sys.argv)

    # Load the UI from the .ui file.
    self.load_ui()

    # Create a controller for the main window.
    self._main_window_controller = MainWindowController(self._main_window)

    # Show the main window.
    self._main_window.show()

  def load_ui(self):
    """This method performs the required magic to load the .ui file for the
    main window using the appropriate method in PySide and PyQt4. After loading,
    we also call the postUiInit() method on the MainWidget so that further setup
    can take place there.

    """
    ui_file = os.path.join(Application.__resource_dir, 'mainwindow.ui')

    if qt.USES_PYSIDE:
      loader = QUiLoader()
      self._main_window = loader.load(ui_file)
    else:
      self._main_window = uic.loadUi(ui_file)

def main():
  """The main entry point for the application. Call this from your script to
  launch the application. This function eventually calls QApplication.exec_()
  so don't expect it to return until the application should exit.

  """
  if 'DEBUG' in os.environ:
    log.setLevel(logging.DEBUG)
  else:
    log.setLevel(logging.INFO)

  # Create the main application
  app = Application()

  # Enter the application main loop
  sys.exit(app.exec_())

# Allow module to be run directly
if __name__ == '__main__':
  main()
