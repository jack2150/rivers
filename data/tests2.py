from django.core.urlresolvers import reverse
from base.tests import TestSetUp
import pandas as pd


class TestCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'FSLR'

    def test_clean_option(self):
        """

        :return:
        """

        #self.client.get(reverse('admin:clean_option', kwargs={'symbol': self.symbol.lower()}))
        self.client.get(reverse('admin:clean_option2', kwargs={'symbol': self.symbol.lower()}))
