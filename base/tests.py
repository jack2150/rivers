from django.contrib.auth.models import User
from django.test import TestCase


class TestSetUp(TestCase):
    def setUp(self):
        TestCase.setUp(self)

        User.objects.create_superuser('root', 'a@a.a', '123456')
        self.client.login(username='root', password='123456')

        print '.' * 100
        print "<%s> currently run: %s" % (self.__class__.__name__, self._testMethodName)
        print '.' * 100 + '\n'

    def tearDown(self):
        """
        remove variables after test
        """
        TestCase.tearDown(self)
        print '\n' + '.' * 100 + '\n'
