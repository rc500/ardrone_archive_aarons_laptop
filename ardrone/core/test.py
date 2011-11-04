import unittest
import doctest

from . import atcommands, config, controlloop, navdata

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(atcommands))
    tests.addTests(doctest.DocTestSuite(config))
    tests.addTests(doctest.DocTestSuite(controlloop))
    tests.addTests(doctest.DocTestSuite(navdata))
    return tests
