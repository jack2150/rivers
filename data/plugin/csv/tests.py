from calendar import month_name
from fractions import Fraction
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying, Treasury
from data.plugin.csv.views import *
from rivers.settings import QUOTE, BASE_DIR
import pandas as pd


class TestCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = ['AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG'][-1]
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

    def test_csv_option_h5_result(self):
        """
        Test csv option full result
        """
        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract/' % self.symbol.lower())
        df_option = db.select('option/%s/raw/data' % self.symbol.lower()).sort_index()
        db.close()

        print 'total option_code in contract: %d' % len(df_contract['option_code'])
        print 'total option_code in option: %d' % len(df_option['option_code'].unique())

        print df_contract.head().to_string(line_width=1000)
        print df_option.head().to_string(line_width=1000)
        self.assertTrue(len(df_contract))
        self.assertTrue(len(df_option))
        self.assertGreater(len(df_option), len(df_contract))
        self.assertEqual(len(df_contract['option_code']), len(df_option['option_code'].unique()))

        specials = ['Standard', 'Weeklys', 'Quarterlys', 'Mini']
        months = [month_name[i + 1][:3].upper() for i in range(12)]
        years = range(8, 20)
        weeks = range(1, 7)
        for index, contract in df_contract.iterrows():
            self.assertIn(self.symbol, contract['option_code'])
            self.assertIn(contract['ex_month'][:3], months)
            if len(contract['ex_month']) == 4:
                self.assertIn(int(contract['ex_month'][3:]), weeks)

            self.assertIn(contract['ex_year'], years)
            self.assertEqual(type(contract['expire']), bool)
            self.assertEqual(type(contract['ex_date']), pd.Timestamp)
            self.assertGreater(contract['missing'], -1)

            # others
            if '$' in contract['others']:
                pass
            else:
                self.assertFalse(len(contract['others']))

            # right
            if '/' in contract['right']:
                try:
                    Fraction(contract['right'])
                except ValueError:
                    raise 'Invalid contract right: %s' % contract['right']
            else:
                try:
                    int(contract['right'])
                except ValueError:
                    raise 'Invalid contract right: %s' % contract['right']

            self.assertIn(contract['special'], specials)
            self.assertEqual(type(contract['strike']), float)

        print 'contract test done, total: %d' % len(df_contract)

        option_code = list(df_contract['option_code'])
        for index, option in df_option.iterrows():
            self.assertIn(option['option_code'], option_code)
            self.assertGreater(option['ask'], -0.01)
            self.assertGreater(option['bid'], -0.01)
            self.assertGreaterEqual(option['ask'], option['bid'])
            self.assertGreater(option['volume'], -1)
            self.assertGreater(option['open_int'], -1)

            self.assertGreater(option['dte'], -1)

        print 'option test done, total: %d' % len(df_option)

    def test_valid_option(self):
        """
        Test validate option data after import
        """
        db = pd.HDFStore(QUOTE)
        df_option = db.select('option/%s/raw/data' % self.symbol.lower()).sort_index()
        df_option = df_option.reset_index()
        db.close()

        print 'run valid_option...'
        valid = valid_option(
            df_option['bid'], df_option['ask'], df_option['volume'],
            df_option['open_int'], df_option['dte']
        )

        self.assertEqual(len(valid), len(df_option))
        df_option['valid'] = valid
        df_valid = df_option.query('valid == 1')
        print 'df_option: %d, df_valid: %d' % (len(df_option), len(df_valid))
        self.assertLessEqual(len(df_valid), len(df_option))

    def test_valid_code(self):
        """
        Test check every option_code in df_contract is in df_option
        """
        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract/' % self.symbol.lower())
        df_contract = df_contract.reset_index()
        df_option = db.select('option/%s/raw/data' % self.symbol.lower()).sort_index()
        db.close()

        valid = valid_code(list(df_contract['option_code']), df_option['option_code'].unique())

        self.assertTrue(np.all(valid))

    def test_valid_contract(self):
        """
        Test validate df_contract every columns
        """
        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract/' % self.symbol.lower())
        df_contract = df_contract.reset_index()
        db.close()

        print 'run valid_contract...'
        valid = valid_contract(self.symbol, df_contract)
        df_contract['valid'] = valid

        self.assertEqual(len(df_contract), len(df_contract.query('valid == 1')))

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