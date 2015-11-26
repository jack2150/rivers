import os
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying, Treasury
from rivers.settings import QUOTE, BASE_DIR
import pandas as pd


class TestCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = ['AIG', 'FSLR', 'SNDK'][0]
        self.underlying = Underlying(
            symbol=self.symbol,
            start='2009-01-01',
            stop='2016-01-01'
        )
        self.underlying.save()

    def tearDown(self):
        TestSetUp.tearDown(self)

    def test_csv_option_h5(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        # self.skipTest('Only test when need!')
        print 'run csv stock import view...'

        #self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': self.symbol}))
        self.client.get(reverse('admin:csv_option_h5', kwargs={'symbol': self.symbol}))

        """
        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract/' % self.symbol.lower())
        df_option = db.select('option/%s/raw/data' % self.symbol.lower()).sort_index()
        db.close()

        print 'total option_code in contract: %d' % len(df_contract['option_code'])
        print 'total option_code in option: %d' % len(df_option['option_code'].unique())

        print df_contract.head().to_string(line_width=1000)
        print df_option.head().to_string(line_width=1000)

        self.assertEqual(len(df_contract['option_code']), len(df_option['option_code'].unique()))

        self.assertTrue(len(df_contract))
        self.assertTrue(len(df_option))

        self.assertGreater(len(df_option), len(df_contract))
        """

    def test_csv_stock_h5(self):
        """
        Test csv stock import into h5 db
        """
        # self.skipTest('Only test when need!')

        print 'run csv stock import view...'
        self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': self.symbol}))

        db = pd.HDFStore(QUOTE)
        df_stock = db.select('stock/thinkback/%s' % self.symbol.lower())
        db.close()
        print df_stock.to_string(line_width=500)
        self.assertTrue(len(df_stock))
