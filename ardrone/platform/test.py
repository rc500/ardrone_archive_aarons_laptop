import unittest
import doctest

# Import the modules which are cross-platform
from . import base, dummy
__modules = [base, dummy]

# Attempt to import the qt platform
try:
  from . import qt
  __modules.append(qt)
except ImportError as e:
  print('Skipping import of qt: %s' % (str(e),))

def load_tests(loader, tests, ignore):
  global __modules
  for m in __modules:
    tests.addTests(doctest.DocTestSuite(m))
  return tests
