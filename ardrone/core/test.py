import unittest
import doctest

from . import atcommands, config, controlloop

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(atcommands))
    tests.addTests(doctest.DocTestSuite(config))
    tests.addTests(doctest.DocTestSuite(controlloop))
    return tests
