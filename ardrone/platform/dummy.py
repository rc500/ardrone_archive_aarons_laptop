"""A dummy connection for testing.

"""
import random
import threading

from . import base

class Connection(base.Connection):
  r""" A simple test connection which can be used to develop applications.

  This connection object doesn't actually connect to the drone. Instead it can
  be used to 'fake' a drone sending navpackets. Commands sent *to* the drone
  are logged by an optional logging function.

  For example:

  >>> from ..core import atcommands as at
  >>> at.reset_sequence()
  >>> a = Connection()
  >>> a.open(1, '127.0.0.1', (None, 1234, None))
  >>> a.put(1, at.ref())
  OUTPUT: 'AT*REF=1,290717696\r'
  >>> def f(x):
  ...   print('Log: %s' % (repr(x),))
  >>> b = Connection(f)
  >>> b.log_cb is f
  True
  >>> b.put(1, at.ref())
  Log: 'AT*REF=2,290717696\r'

  """

  def __init__(self, log_cb = None, *args, **kwargs):
    """ Create the dummy connection object.

    """
    base.Connection.__init__(self, *args, **kwargs)
    self.log_cb = log_cb

  def put(self, connection, packet):
    r""" Send the command string to the drone over the network.

    """

    if self.log_cb is None:
      print('OUTPUT: %s' % (repr(str(packet)),))
    else:
      self.log_cb(str(packet))
