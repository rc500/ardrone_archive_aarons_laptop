#
#   Copyright 2011, Rich Wareham <rjw57@cantab.net>, Aaron Croucher <aaron.croucher@gmail.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import json, os, sys, time

# This makes soure the path which python uses to find things when using import
# can find all our code.
this_file_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(this_file_dir, '..')))

# The magic runes required to import the Qt modules in a platform-independent
# way
import ardrone.util.qtcompat as qt
QtCore = qt.import_module('QtCore')
QtNetwork = qt.import_module('QtNetwork')

class Logger(object):
	"""
	A logger which parses control packets and logs the sensor readings determined by the variables which a particular instance of this object is initiated with.
	The logged values are logged in a file with two columns: time and value.
	"""
	def __init__(self, value, port='5561', log_file='log_dump.dat'):
		# Store parameters
		self._port = port
		self._value = value
		self._log_file = open(log_file, 'w')

	def log(self,data):
		"""
		Called with data packet which it interprets and logs desired values when they appear.
		"""
		# Some hack to account for PySide vs. PyQt differences
		if qt.USES_PYSIDE:
			data = data.data()
		  
		# Parse the packet
		packet = json.loads(data.decode())

		# Store the value in the packet (if it is present) and the current time
		if self._value in packet and self._log_file is not None:
			self._log_file.write(str(time.time()))
			self._log_file.write(' ')
			self._log_file.write(str(packet[self._value]))
			self._log_file.write('\n')

if __name__ == '__main__':
	logger.main()
