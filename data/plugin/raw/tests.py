import os
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.plugin.csv.views import *


class TestReverseCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = ['AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG'][0]
        self.underlying = Underlying(
            symbol=self.symbol,
            start='2009-01-01',
            stop='2016-01-01'
        )
        self.underlying.save()

    def test_csv_option_h5x(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        # self.skipTest('Only test when need!')
        print 'run csv stock import view...'

        # self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': self.symbol}))
        self.client.get(reverse('admin:csv_option_h5x', kwargs={'symbol': self.symbol}))

