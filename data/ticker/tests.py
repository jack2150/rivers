import os
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying
from rivers.settings import QUOTE_DIR
import pandas as pd


class TestWebYahooMinute(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'
        self.underlying = Underlying(
            symbol=self.symbol,
            start_date='2009-01-01',
            stop_date='2009-03-01'
        )
        self.underlying.save()

    def test_web_yahoo_minute(self):
        """
        Test import thinkback csv option into db
        """
        # self.skipTest('Only test when need!')
        self.client.get(reverse('admin:web_yahoo_minute_data', kwargs={
            'symbol': self.symbol
        }))

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_minute = db.select('ticker/yahoo/minute1')
        db.close()

        print df_minute.tail()

    def test_web_yahoo_minute_mass(self):
        """
        Test import thinkback csv option into db
        """
        symbols = ['USO', 'IBM', 'FSLR', 'JPM', 'WFC', 'IWM', 'TZA', 'UVXY']
        # self.skipTest('Only test when need!')

        for symbol in symbols:
            print 'symbol: %s' % symbol,
            underlying = Underlying(
                symbol=symbol,
                start_date='2009-01-01',
                stop_date='2009-03-01'
            )
            underlying.save()
            self.client.get(reverse('admin:web_yahoo_minute_data', kwargs={
                'symbol': symbol
            }))

            path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
            db = pd.HDFStore(path)
            df_minute = db.select('ticker/yahoo/minute1')
            db.close()

            print 'df_minute: %d' % len(df_minute)
            print df_minute.tail()
            self.assertTrue(len(df_minute))

            print '-' * 70
