import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivers.settings")
import django
django.setup()

# noinspection PyUnresolvedReferences
from rivers import settings
from unittest import TestCase as UnitTestCase
from django.test import Client
from django.test.utils import setup_test_environment
import sys


# remember to set default test runner in pycharm
class TestUnitSetUp(UnitTestCase):
    def setUp(self):
        UnitTestCase.setUp(self)
        setup_test_environment()

        if 'utrunner' not in sys.argv[0]:
            self.skipTest('Only can run with unittest.')

        self.client = Client()
        self.client.login(username='bvc100x', password='qwer1234')

        print '.' * 100
        print "<%s> currently run: %s" % (self.__class__.__name__, self._testMethodName)
        print '.' * 100 + '\n'

    def tearDown(self):
        """
        remove variables after test
        """
        UnitTestCase.tearDown(self)
        print '\n' + '.' * 100 + '\n'
