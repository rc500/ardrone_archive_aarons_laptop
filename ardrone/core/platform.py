"""Base classes for platform-specific functionality.

"""

class Connection(object):
  """Sub classes should override the put method at a minimum. Usually the
  connect method will be overridden as well. Optionally the disconnect method
  may be overridden.

  When a packet of navdata from the drone arrives, it should be passed to the
  got_navdata method.

  The navdata_cb attribute of the object gives the current navdata callable
  which will be called when a packet arrives.

  >>> p = None
  >>> def f(packet):
  ...   global p
  ...   p = packet
  >>> c = Connection(navdata_cb=f)
  >>> p is None
  True
  >>> c.navdata_cb is f
  True
  >>> c.connect()
  True
  >>> c.put('one')
  Traceback (most recent call last):
    File "<stdin>", line 1, in ?
  NotImplementedError: You must override the put method.
  >>> c.got_navdata('hello')
  >>> p is 'hello'
  True
  >>> c.got_navdata('world')
  >>> p is 'world'
  True
  >>> c.navdata_cb = None
  >>> c.got_navdata('foo')
  >>> p is 'foo'
  False
  >>> c.disconnect()

  """

  def __init__(self,  navdata_cb=None):
    """Initialise the connection. navdata_cb may optionally be a callable which
    is called when a navdata packet arrives.
    
    >>> Connection() # doctest: +ELLIPSIS
    <platform.Connection object at 0x...>

    """
    self.navdata_cb = navdata_cb

  def connect(self):
    """Optionally override this method to connect to the drone. Return True if
    connection was successful, False otherwise. Calling put before this method
    is called or if this method returns False is undefined behaviour. No
    navdata packets should be sent via got_navdata until this method is called.

    The default implementation returns True.

    >>> c = Connection()
    >>> c.connect()
    True
    >>> c.disconnect()
    
    """
    return True

  def disconnect(self):
    """Optionally override this method to disconnect to the drone. Calling put
    after this method is undefined behaviour. Depending on network effects,
    however, navdata packets may still arrive after this method is called.

    The default implementation does nothing.

    >>> c = Connection()
    >>> c.connect()
    True
    >>> c.disconnect()

    """
    pass

  def put(self, command_string):
    """Override this method to send the command string passed to the drone.

    The default implementation will throw a NotImplementedError.

    >>> c = Connection()
    >>> c.connect()
    True
    >>> c.put('one')
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    NotImplementedError: You must override the put method.
    >>> c.disconnect()
    
    """
    raise NotImplementedError('You must override the put method.')

  def got_navdata(self, packet):
    """Call this method when a navdata packet from the drone has arrived. Pass
    the raw packet in as a sequence of bytes.

    >>> p = None
    >>> def f(packet):
    ...   global p
    ...   p = packet
    >>> c = Connection(navdata_cb=f)
    >>> c.connect()
    True
    >>> c.got_navdata('hello')
    >>> p is 'hello'
    True
    >>> c.got_navdata('world')
    >>> p is 'world'
    True
    >>> c.disconnect()

    """
    if self.navdata_cb is not None:
      self.navdata_cb(packet)
