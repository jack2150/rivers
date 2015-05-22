import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rivers.settings")
# noinspection PyUnresolvedReferences
from rivers import settings
from unittest import TestCase as UnitTestCase


class TestUnitSetUp(UnitTestCase):
    def setUp(self):
        UnitTestCase.setUp(self)

        print '.' * 100
        print "<%s> currently run: %s" % (self.__class__.__name__, self._testMethodName)
        print '.' * 100 + '\n'

    def tearDown(self):
        """
        remove variables after test
        """
        UnitTestCase.tearDown(self)
        print '\n' + '.' * 100 + '\n'