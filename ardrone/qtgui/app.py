"""Main application loop for the GUI program.

"""

import os
import sys

from PyQt4 import QtCore, QtGui, uic

__resource_dir = os.path.dirname(__file__)

def main():
	app = QtGui.QApplication(sys.argv)
	window = uic.loadUi(os.path.join(__resource_dir, 'main_window.ui'))
	window.show()
	sys.exit(app.exec_())
