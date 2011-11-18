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
