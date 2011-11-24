"""
Support for Qt applications
===========================

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

class ControlServer(object):
  """A server which can listen for control messages and transmit status
  information.

  Usage example
  ------------
  
  Create a Qt event loop:

  >>> from ..util import qtcompat as qt
  >>> QtCore = qt.import_module('QtCore')
  >>> app = QtCore.QCoreApplication([])

  Create a server:

  >>> s = ControlServer()

  Run the server (stopping after 1 second).

  >>> import multiprocessing as mp
  >>> p = mp.Process(target=app.exec_)
  >>> QtCore.QTimer.singleShot(1000, app, QtCore.SLOT('quit()'))
  >>> p.start()

  Create a client:

  >>> c = ControlClient()
  >>> c.wait_for_connect()
  True

  Wait for the server to exit.

  >>> p.join()
  >>> p.exitcode
  0

  Check we disconnected.

  >>> c.wait_for_disconnect()
  True

  """

  """The default port to listen on."""
  CONTROL_PORT = 5570

  def __init__(self, port=CONTROL_PORT):
    """Create a new server listening on *port* for new connections."""

    self._server = QtNetwork.QTcpServer()
    self._server.newConnection.connect(self._new_connection)
    self._connections = []

    if not self._server.listen(port = port):
      raise RuntimeError('Cannot start control server: ' + self._server.errorString())

  def _new_connection(self):
    """Called when a connection is made to the server."""

    while self._server.hasPendingConnections():
      next_connection = self._server.nextPendingConnection()
      next_connection.readyRead.connect(self._ready_read)
      next_connection.disconnected.connect(self._connection_lost)
      self._connections.append(next_connection)

  def _ready_read(self, connection):
    print(connection)

  def _connection_lost(self, connection):
    self._connections.remove(connection)

class ControlClient(object):
  """A simple TCP client for sending control commands to and getting data back
  from the control server.

  Instances of this class have a boolean *connected* attribute which can be
  used to query the connection state.

  """

  def __init__(self,
      host_name='127.0.0.1',
      port=ControlServer.CONTROL_PORT):
    """Initialise the control client and connect to the named host and port."""

    self._socket = QtNetwork.QTcpSocket()
    self._socket.connected.connect(self._connected)
    self._socket.disconnected.connect(self._disconnected)
    self.connected = False
    self._socket.connectToHost(host_name, port)

  def wait_for_connect(self, timeout_msecs=30000):
    """If not connected, wait for a connection.
    
    *timeout_msecs* is the maximum number of milliseconds to wait for a
    connection.

    Returns True iff the connection was made or if the client was already
    connected.

    """

    if self.connected:
      return True

    # True == at he beginning because a special qt bool wrapper is returned by
    # PySide.
    return True == self._socket.waitForConnected(timeout_msecs)

  def wait_for_disconnect(self, timeout_msecs=30000):
    """If not diconnected, wait for a connection to be broken.
    
    *timeout_msecs* is the maximum number of milliseconds to wait for a
    disconnection.

    Returns True iff the connection was disconnected or if the client was already
    disconnected.

    """

    if not self.connected:
      return True

    # True == at he beginning because a special qt bool wrapper is returned by
    # PySide.
    return True == self._socket.waitForDisconnected(timeout_msecs)

  def _connected(self):
    self.connected = True

  def _disconnected(self):
    self.connected = False


class Connection(base.Connection):
  """A Qt implementation of the UDP connection to the drone.

  Firstly, start a dummy UDP server.

  >>> import multiprocessing as mp
  >>> import socket
  >>> from .. import udpechoserver
  >>> p = mp.Process(target=udpechoserver.serve)
  >>> p.start()

  Create a Qt event loop.

  >>> from ..util import qtcompat as qt
  >>> QtCore = qt.import_module('QtCore')
  >>> app = QtCore.QCoreApplication([])

  Here we use the bind port of 5555 since the drone server binds to 5556.
  Furthermore, we set the navdata_bind_port to 5556 so that we see the replies
  from the server.

  >>> data_log = []
  >>> c = Connection()
  >>> c.open(1, ('127.0.0.1', 5556), None)
  >>> c.open(2, ('127.0.0.1', 1234), (None, 5555, lambda d: data_log.append(d)))

  Create some commands to send.

  >>> from ..core import atcommands as at
  >>> r1 = at.ref()
  >>> r2 = at.config('foo', 'bar')

  Send the commands.

  >>> c.put(1,r1)
  >>> c.put(1,r2)

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
  def __init__(self, *args, **kwargs):
    super(Connection, self).__init__(*args, **kwargs)

    # tuples giving the socket, send host and send port
    self._sockets = {}

  def open(self, connection, send, bind=None):
    super(Connection, self).open(connection, send, bind)

    socket = QUdpSocket()

    if bind is not None:
      if bind[0] is None:
        bind_host = QtNetwork.QHostAddress(QtNetwork.QHostAddress.Any)
      else:
        bind_host = QtNetwork.QHostAddress(bind[0])
      logging.info('Qt: binding to UDP host/port: %s/%s' % (bind_host.toString(), bind[1]))
      if not socket.bind(bind_host, bind[1]):
        logging.error('error binding UDP server: ' + socket.errorString())
        return #raise base.ConnectionError(socket.errorString())

      # Bind a handler to the readtRead signal
      def ready_read():
        while socket.hasPendingDatagrams():
          #logging.info('Got datapacket on connection: %i' % (connection,))
          sz = socket.pendingDatagramSize()
          (data, host, port) = socket.readDatagram(sz)
          if qt.USES_PYSIDE:
            # PySide returns a QByteArray
            self.got_packet(connection, data.data())
          else:
            self.got_packet(connection, data)

      QObject.connect(socket, SIGNAL('readyRead()'), ready_read)

    self._sockets[connection] = (socket, QtNetwork.QHostAddress(send[0]), send[1])

  def put(self, connection, data):
    socket, host, port = self._sockets[connection]
    if -1 == socket.writeDatagram(data, host, port):
      logging.error('Failed to send to %s:%s. Error was: %s' %
          (host.toString(), port, socket.errorString()))
      raise base.ConnectionError(socket.errorString())
