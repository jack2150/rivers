from django.test import TestCase


class TestSetUp(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        print '.' * 100
        print "<%s> currently run: %s" % (self.__class__.__name__, self._testMethodName)
        print '.' * 100 + '\n'

    def tearDown(self):
        """
        remove variables after test
        """
        TestCase.tearDown(self)
        print '\n' + '.' * 100 + '\n'
