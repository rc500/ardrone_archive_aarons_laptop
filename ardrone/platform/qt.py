"""A connection based on PyQt4

"""
import logging

from ..util import qtcompat as qt

try:
  QtCore = qt.import_module('QtCore')
  QtNetwork = qt.import_module('QtNetwork')

  # Since we only use a few classes, extract them for convenience
  QObject = QtCore.QObject
  SIGNAL = QtCore.SIGNAL
  QHostAddress = QtNetwork.QHostAddress
  QUdpSocket = QtNetwork.QUdpSocket
except Exception as e:
  raise ImportError(str(e))

from . import base

class Connection(base.Connection):
  """A Qt implementation of the UDP connection to the drone.

  Firstly, start a dummy drone server.

  >>> import multiprocessing as mp
  >>> import socket
  >>> from .. import dummydrone
  >>> p = mp.Process(target=dummydrone.serve)
  >>> p.start()

  Create a Qt event loop.

  >>> from ..util import qtcompat as qt
  >>> QtCore = qt.import_module('QtCore')
  >>> app = QtCore.QCoreApplication([])

  Here we use the bind port of 5555 since the drone server binds to 5556.
  Furthermore, we set the navdata_bind_port to 5556 so that we see the replies
  from the server.

  >>> data_log = []
  >>> c = Connection(
  ...   navdata_cb=lambda d: data_log.append(d),
  ...   drone_host='127.0.0.1',
  ...   at_bind_port=5555, navdata_bind_port=5556)

  Connect to the drone/

  >>> c.connect()
  True

  Create some commands to send.

  >>> from ..core import atcommands as at
  >>> r1 = at.ref()
  >>> r2 = at.config('foo', 'bar')

  Send the commands.

  >>> c.put(r1)
  >>> c.put(r2)

  Wait for the event loop to finish.

  >>> QtCore.QTimer.singleShot(500, app.quit)
  >>> app.exec_()
  0

  See if our server echoed the commands back.

  >>> r1 in data_log
  True
  >>> r2 in data_log
  True

  Clear up the server

  >>> p.terminate()

  """
  def __init__(self, bind_host=QHostAddress.Any,
      drone_host='192.168.1.1',
      at_port=5556, at_bind_port=5556,
      navdata_bind_port=5554,
      *args, **kwargs):
    base.Connection.__init__(self, *args, **kwargs)

    self._bind_host = QHostAddress(bind_host)
    self._drone_host = QHostAddress(drone_host)

    self._at_port = at_port
    self._at_bind_port = at_bind_port
    self._at_socket = QUdpSocket()

    self._navdata_bind_port = navdata_bind_port
    self._navdata_socket = QUdpSocket()

    # Start the server
    if not self._navdata_socket.bind(self._bind_host, self._navdata_bind_port):
      logging.error('error binding navdata port: ' + self._navdata_socket.errorString())
      raise base.ConnectionError(self._navdata_socket.errorString())
    QObject.connect(self._navdata_socket, SIGNAL('readyRead()'), self._navDataReadyRead)

  def connect(self):
    if not self._at_socket.bind(self._bind_host, self._at_bind_port):
      logging.error('error binding AT command port: ' + self._at_socket.errorString())
      return False

    return True

  def put(self, cmd):
    if -1 == self._at_socket.writeDatagram(cmd, self._drone_host, self._at_port):
      logging.error('Failed to send to %s:%s. Error was: %s' %
          (self._drone_host.toString(), self._at_port, self._at_socket.errorString()))
      raise base.ConnectionError(self._at_socket.errorString())
  
  def _navDataReadyRead(self):
    sz = self._navdata_socket.pendingDatagramSize()
    (data, host, port) = self._navdata_socket.readDatagram(sz)
    if qt.USES_PYSIDE:
      # PySide returns a QByteArray
      self.got_navdata(data.data())
    else:
      self.got_navdata(bytes.decode(data))
