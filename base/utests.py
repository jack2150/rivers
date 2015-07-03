import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivers.settings")
# noinspection PyUnresolvedReferences
from rivers import settings
from unittest import TestCase as UnitTestCase
from django.test import Client
from django.test.utils import setup_test_environment


class TestUnitSetUp(UnitTestCase):
    def setUp(self):
        UnitTestCase.setUp(self)
        setup_test_environment()

        self.client = Client()
        self.client.login(username='jack', password='qwer1234')

        print '.' * 100
        print "<%s> currently run: %s" % (self.__class__.__name__, self._testMethodName)
        print '.' * 100 + '\n'

    def tearDown(self):
        """
        remove variables after test
        """
        UnitTestCase.tearDown(self)
        print '\n' + '.' * 100 + '\n'