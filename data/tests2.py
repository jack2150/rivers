"""
1. create a underlying data
2. create
"""
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying, Treasury
from data.views2 import TreasuryImportForm, EventImportForm
from rivers.settings import QUOTE, BASE_DIR
import pandas as pd


class TestCsvToHDF(TestSetUp):
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

    def tearDown(self):
        TestSetUp.tearDown(self)

    def test_csv_option_import_view(self):
        """
        Test import thinkback csv option into db
        """
        print 'run csv stock import view...'
        self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': self.symbol}))
        self.client.get(reverse('admin:csv_option_h5', kwargs={'symbol': self.symbol}))

    def test123(self):
        db = pd.HDFStore(QUOTE)

        #df_missing = db.select('option/%s/contract' % self.symbol.lower(), 'missing > 0')
        #print df_missing.to_string(line_width=500)

        #df_index = db.select('option/aig/index', 'index == Timestamp("20100113")')
        #df_index = db.select('option/aig/index', 'option_code == %r' % 'IKG101120P38')
        #print df_index.to_string(line_width=500)

        df_stock = db.select('stock/google/%s' % self.symbol.lower())
        print df_stock.to_string(line_width=500)

        db.close()

    def test_web_treasury_form(self):
        form = TreasuryImportForm(data=self.data)

        print form.is_valid()

    def test_web_treasury_h5(self):
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
    def test_earning_import_form(self):
        """
        Test verify event form and handle file upload then verify earning
        """
        path = os.path.join(BASE_DIR, 'files', 'fidelity', 'earnings')

        for symbol in ('YUM',):  # ('JPM', 'DDD'):
            print 'running symbol:', symbol
            form = EventImportForm(
                {'symbol': symbol, 'event': 'earning'},
                {'fidelity_file': SimpleUploadedFile(
                    '%s _ Earnings - Fidelity' % symbol,
                    open(os.path.join(path, '%s _ Earnings - Fidelity.html' % symbol)).read()
                )}
            )

            self.assertTrue(form.is_valid())
            form.import_earning()

            db = pd.HDFStore(QUOTE)
            df_earning = db.select('earning/%s' % symbol.lower())
            print df_earning.to_string(line_width=600)
            self.assertTrue(len(df_earning))
            db.close()

    def test_dividend_import_form(self):
        path = os.path.join(BASE_DIR, 'files', 'fidelity', 'dividends')

        for symbol in ('JPM', 'AIG'):
            print 'running symbol:', symbol
            form = EventImportForm(
                {'symbol': symbol, 'event': 'dividend'},
                {'fidelity_file': SimpleUploadedFile(
                    '%s _ Dividends - Fidelity' % symbol,
                    open(os.path.join(path, '%s _ Dividends - Fidelity.html' % symbol)).read()
                )}
            )
            #print form.errors
            self.assertTrue(form.is_valid())
            form.insert_dividend()

            db = pd.HDFStore(QUOTE)
            df_dividend = db.select('dividend/%s' % symbol.lower())
            print df_dividend.to_string(line_width=600)
            self.assertTrue(len(df_dividend))
            db.close()
