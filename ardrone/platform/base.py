"""Base classes for platform-specific functionality.

"""

class ConnectionError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg


class Connection(object):
  """A base class for allowing platform independent UDP connections and UDP servers.

  Since a UDP 'server' needs to sit in a loop waiting on a connection, it makes
  sense to re-use the event loop from various GUI toolkits, the various
  sub-classes of this class do this.

  To open a connection, call the open method. This may send port and,
  optionally, a bind port and callable pair to start a UDP server listening on
  that port. The connection is identified by some hashable object.

  The put method is used to send a packet over a connection. This sends a
  packet of data to the send port fo the connection.

  Sub classes should override the put method at a minimum. Usually the
  connect method will be overridden as well. Optionally the disconnect method
  may be overridden.

  All connection methods may raise a ConnectionError if there is some problem
  sending the data.

  >>> p = None
  >>> def f(packet):
  ...   global p
  ...   p = packet
  >>> c = Connection()
  >>> p is None
  True
  >>> c.open(1, ('127.0.0.1', 1234), (None, 5678, f))
  >>> c.put(1, 'one')
  Traceback (most recent call last):
    File "<stdin>", line 1, in ?
  NotImplementedError: You must override the put method.
  >>> c.got_packet(1, 'hello')
  >>> p is 'hello'
  True
  >>> c.got_packet(1, 'world')
  >>> p is 'world'
  True

  """

  def __init__(self):
    """Initialise the connection.
    
    >>> Connection() # doctest: +ELLIPSIS
    <ardrone.platform.base.Connection object at 0x...>

    """
    self._connection_callables = {}

  def open(self, connection, send, bind=None):
    """Override this method in sub-classes to open a connection.

    send is a pair of a string and integer giving the hostname/ip of the host
    to send to and which port to send to.

    bind is optionally a triplet (host,port,callable) which is a host interface
    and port to bind to and a callable to call when data arrives on that port.
    If the host is None, bind to all interfaces.

    Derrived classes *must* call the base implementation.

    """
    if bind is not None:
      self._connection_callables[connection] = bind[2]


  def put(self, connection, data):
    """Override this method to send the command string passed to the drone.

    The default implementation will throw a NotImplementedError.

    """
    raise NotImplementedError('You must override the put method.')

  def got_packet(self, connection, packet):
    """Call this method when a navdata packet from the drone has arrived. Pass
    the raw packet in as a sequence of bytes.

    """
    if connection in self._connection_callables:
      cb = self._connection_callables[connection]
      if cb is not None:
        cb(packet)
