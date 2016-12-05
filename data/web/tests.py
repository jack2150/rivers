import os

from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying, Treasury
from rivers.settings import QUOTE_DIR
import pandas as pd


class TestWebStockTreasury(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'
        self.underlying = Underlying(
            symbol=self.symbol,
            start_date='2009-01-01',
            stop_date='2009-03-01'
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
        # self.skipTest('Only test when need!')

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        print 'run csv stock import view...'
        for source in ('google', 'yahoo'):
            self.client.get(reverse('admin:web_stock_h5', kwargs={
                'symbol': self.symbol, 'source': source
            }))

            db = pd.HDFStore(path)
            df_stock = db.select('stock/%s' % source)
            db.close()

            self.assertTrue(len(df_stock))

    def test_show_web_data(self):
        """
        Simple show web data
        """
        self.symbol = 'SPY'
        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_stock = db.select('stock/%s' % 'google')
        db.close()

        df_stock['pct_chg'] = df_stock['close'].pct_change()

        # print df_stock
        #print df_stock[df_stock.index == '2015-11-17']
        f = open('spy.txt', mode='w')
        f.write(df_stock.to_csv())
        f.close()

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

        db = pd.HDFStore(QUOTE_DIR)
        df_rate = db.select('treasury/%s' % treasury.to_key())
        db.close()

        self.assertTrue(len(df_rate))
        print df_rate.tail()
