from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying
from rivers.settings import QUOTE
import numpy as np
import pandas as pd
from views import *


class TestCsvRawOption(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbols = [
            'AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG',
            'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG',
            'DAL', 'DIS', 'EA', 'EBAY', 'FB'
        ]

    def save_underlying(self, symbol):
        self.underlying = Underlying(
            symbol=symbol,
            start='2009-01-01',
            stop='2016-01-01'
        )
        self.underlying.save()

    def test_csv_raw_option(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        symbol = self.symbols[0]

        # self.skipTest('Only test when need!')
        print 'run csv_raw_option...', symbol
        self.save_underlying(symbol)

        # self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
        self.client.get(reverse('admin:csv_raw_option', kwargs={'symbol': symbol.lower()}))

    def test_merge_raw_option(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        symbol = self.symbols[0]

        # self.skipTest('Only test when need!')
        print 'run csv_raw_option...', symbol
        self.save_underlying(symbol)

        # self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
        # csv_raw_option(symbol.lower())
        # merge_raw_option(symbol.lower())
        merge_option_others(symbol.lower())

    def test_both_others_same(self):
        """

        :return:
        """
        symbol = self.symbols[0]

        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract' % symbol.lower())
        df_option = db.select('option/%s/raw/data' % symbol.lower())
        df_others0 = db.select('test/%s/data/others' % symbol.lower())
        db.close()

        df_others1 = pd.merge(
            df_option,
            df_contract.query('others != ""'),
            how='inner',
            on='option_code'
        )

        print len(df_others0)
        print len(df_others1)












