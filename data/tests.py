from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying
from rivers.settings import QUOTE
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

    def test_csv_stock_h5(self):
        """
        Test csv stock import into h5 db
        """
        self.skipTest('Only test when need!')

        print 'run csv stock import view...'
        self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': self.symbol}))

        db = pd.HDFStore(QUOTE)
        df_stock = db.select('stock/thinkback/%s' % self.symbol.lower())
        db.close()
        print df_stock.to_string(line_width=500)
        self.assertTrue(len(df_stock))


class TestUnderlyingManage(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

        try:
            self.underlying = Underlying.objects.get(symbol=self.symbol)
        except ObjectDoesNotExist:
            self.underlying = Underlying(symbol=self.symbol)
            self.underlying.start_date = '2015-04-01'
            self.underlying.stop_date = '2015-04-30'
            self.underlying.save()

    def test_set_underlying(self):
        """
        Test set_underlying_updated view
        """
        for action in ('updated', 'optionable'):
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
        underlying.start_date = '2015-05-20'
        underlying.stop_date = '2015-05-30'
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
