import unittest
import doctest

__modules = []

# Attempt to import the qt platform
try:
  from ..util import qtcompat

  from . import app, mainwindowcontroller
  __modules.extend([app, mainwindowcontroller])
except ImportError as e:
  print('Skipping qtgui tests since Qt could not be imported: %s' % (str(e),))

def load_tests(loader, tests, ignore):
  global __modules
  for m in __modules:
    tests.addTests(doctest.DocTestSuite(m))
  return tests
