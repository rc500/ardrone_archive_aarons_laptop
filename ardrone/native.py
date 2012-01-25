"""Module to handle importing native modules via ctypes.

"""

import ctypes
import os
import logging

log = logging.getLogger()

def load_dll(name):
  """Attempt to load a DLL from the lib directory under ardrone/native.
  Appropriate platform suffices are attempted.

  *name* is the filename (without platform extension, e.g. ".dll", ".so") of
  the DLL to load.

  Returns a ctyles CDLL instance if successful or None on failure.

  """

  # Find out which directour _this_ file is in
  this_dir = os.path.abspath(os.path.dirname(__file__))

  # And hence the native libdir
  native_dir = os.path.join(this_dir, 'native')

  for lib_dir in ['', 'bin', 'lib']:
    for suffix in ['', '.so', '.dll']:
      dllpath = os.path.join(native_dir, lib_dir, name + suffix)
      if os.path.exists(dllpath):
        try:
          dll = ctypes.CDLL(dllpath)
          return dll
        except OSError as e:
          # Report DLL load errors and try to continue
          log.warning('Error loading %s: %s' % (dllpath, str(e)))

  log.error('Failed to find or load DLL "%s" in the native directory.' % (name,))
  return None
