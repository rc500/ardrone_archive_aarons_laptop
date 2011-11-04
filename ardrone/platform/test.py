import unittest
import doctest

from . import base, dummy

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(base))
    tests.addTests(doctest.DocTestSuite(dummy))
    return tests
