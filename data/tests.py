import os
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying, Treasury
from data.views import get_dte_date
from rivers.settings import QUOTE, BASE_DIR
import pandas as pd


class TestCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'FSLR'
        self.underlying = Underlying(
            symbol=self.symbol,
            start='2010-04-26',
            stop='2010-06-01'
        )
        self.underlying.save()

    def tearDown(self):
        TestSetUp.tearDown(self)

    def test_get_dte_date(self):
        #print get_dte_date('JAN', 10)
        for i in range(10):
            break
        else:
            print 1

    def test_csv_option_h5(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        #self.skipTest('Only test when need!')

        print 'run csv stock import view...'

        self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': self.symbol}))
        self.client.get(reverse('admin:csv_option_h5', kwargs={'symbol': self.symbol}))

        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/contract/' % self.symbol.lower())
        df_option = db.select('option/%s/raw/' % self.symbol.lower()).sort_index()
        db.close()

        self.assertTrue(len(df_contract))
        self.assertTrue(len(df_option))

        self.assertGreater(len(df_option), len(df_contract))

        # todo: wfc option import problem

    def test_csv_stock_h5(self):
        """
        Test csv stock import into h5 db
        """
        #self.skipTest('Only test when need!')

        print 'run csv stock import view...'
        self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': self.symbol}))

        db = pd.HDFStore(QUOTE)
        df_stock = db.select('stock/thinkback/%s' % self.symbol.lower())
        db.close()
        print df_stock.to_string(line_width=500)
        self.assertTrue(len(df_stock))


class TestWebStockTreasury(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'SNDK'
        self.underlying = Underlying(
            symbol=self.symbol,
            start='2009-01-01',
            stop='2009-03-01'
        )
        self.underlying.save()

        self.data = {
            'url': 'http://www.federalreserve.gov/datadownload/Output.aspx?'
                   'rel=H15&series=e30653a4b627e9d1f2490a0277d9f1ac&lastObs='
                   '&from=&to=&filetype=csv&label=include&layout=seriescolumn'
        }

    def test_web_stock_h5(self):
        """
        Test import thinkback csv option into db
        """
        self.skipTest('Only test when need!')

        print 'run csv stock import view...'
        for source in ('google', 'yahoo'):
            self.client.get(reverse('admin:web_stock_h5', kwargs={
                'symbol': self.symbol, 'source': source
            }))

            db = pd.HDFStore(QUOTE)
            df_stock = db.select('stock/%s/%s' % (source, self.symbol.lower()))
            db.close()

            self.assertTrue(len(df_stock))

    def test_web_treasury_h5(self):
        """
        Test web treasury url import into h5 db
        """
        self.skipTest('Only test when need!')

        print 'run get treasury h5...'
        self.client.post(
            reverse('admin:web_treasury_h5'),
            data=self.data
        )

        treasury = Treasury.objects.first()
        self.assertTrue(treasury.id)

        db = pd.HDFStore(QUOTE)
        df_rate = db.select('treasury/%s' % treasury.to_key())
        db.close()

        self.assertTrue(len(df_rate))
        print df_rate.tail()


class TestEventImport(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        for symbol in ('YUM', 'AIG', 'JPM'):
            underlying = Underlying()
            underlying.symbol = symbol
            underlying.start = pd.Timestamp('20010101').date()
            underlying.stop = pd.Timestamp('20160101').date()
            underlying.save()

    def test_earning_import_form(self):
        """
        Test verify event form and handle file upload then verify earning
        """
        for symbol in ('YUM',):  # ('JPM', 'DDD'):
            print 'running symbol:', symbol
            self.client.get(reverse('admin:html_event_import', kwargs={'symbol': symbol}))

            db = pd.HDFStore(QUOTE)
            df_earning = db.select('event/earning/%s' % symbol.lower())
            print df_earning.to_string(line_width=600)
            self.assertTrue(len(df_earning))
            db.close()

            db = pd.HDFStore(QUOTE)
            df_dividend = db.select('event/dividend/%s' % symbol.lower())
            print df_dividend.to_string(line_width=600)
            self.assertTrue(len(df_dividend))
            db.close()


class TestUnderlyingManage(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

        try:
            self.underlying = Underlying.objects.get(symbol=self.symbol)
        except ObjectDoesNotExist:
            self.underlying = Underlying(symbol=self.symbol)
            self.underlying.start = '2015-04-01'
            self.underlying.stop = '2015-04-30'
            self.underlying.save()

    def test_set_underlying(self):
        """
        Test set_underlying_updated view
        """
        for action in ('updated', 'optionable'):
            #print action
            self.assertFalse(getattr(self.underlying, action))
            print 'underlying before:', getattr(self.underlying, action)

            response = self.client.get(reverse(
                'admin:set_underlying', kwargs={
                    'symbol': self.symbol.lower(), 'action': action
                })
            )

            # check redirect
            self.assertIn(
                reverse('admin:data_underlying_changelist'),
                response.url
            )
            self.assertEqual(response.status_code, 302)

            self.underlying = Underlying.objects.get(symbol=self.symbol)
            self.assertTrue(getattr(self.underlying, action))
            print 'underlying updated:', getattr(self.underlying, action), '\n'


class TestTruncateSymbol(TestSetUp):
    def test_truncate_symbol_view(self):
        """
        Test truncate symbol view
        """
        symbol = 'AIG0'
        underlying = Underlying(symbol=symbol)
        underlying.start = '2015-05-20'
        underlying.stop = '2015-05-30'
        underlying.thinkback = 213
        underlying.google = 321
        underlying.yahoo = 123
        underlying.contract = 17000
        underlying.option = 440000
        underlying.dividend = 9
        underlying.earning = 40
        underlying.save()

        # test redirect and underlying set into 0
        print 'run truncate symbol...'
        response2 = self.client.post(
            reverse('admin:truncate_symbol', kwargs={'symbol': symbol}),
            data={'symbol': symbol}
        )

        self.assertIn(
            reverse('admin:data_underlying_changelist'),
            response2.url
        )
        self.assertEqual(response2.status_code, 302)

        underlying = Underlying.objects.get(symbol=symbol)
        self.assertFalse(underlying.thinkback)
        self.assertFalse(underlying.google)
        self.assertFalse(underlying.yahoo)
        self.assertFalse(underlying.contract)
        self.assertFalse(underlying.option)
        self.assertFalse(underlying.dividend)
        self.assertFalse(underlying.earning)