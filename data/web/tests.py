from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying, Treasury
from rivers.settings import QUOTE
import pandas as pd


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
