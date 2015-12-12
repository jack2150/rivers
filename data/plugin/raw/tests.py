import os
from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.models import Underlying
from data.plugin.raw.views import *
from rivers.settings import QUOTE


class TestReverseCsvToH5(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbols = [
            'AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG',
            'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG',
            'DAL', 'DIS', 'EA', 'EBAY', 'FB'
        ]

    def test_mass_csv_option_h5x(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        # self.skipTest('Only test when need!')
        print 'run mass csv option import 2...'

        for symbol in self.symbols[-4:-3]:
            self.underlying = Underlying(
                symbol=symbol,
                start='2009-01-01',
                stop='2016-01-01'
            )
            self.underlying.save()
            self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
            self.client.get(reverse('admin:csv_option_h5', kwargs={'symbol': symbol}))

    def test_csv_option_h5x(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        symbol = self.symbols[0]

        # self.skipTest('Only test when need!')
        print 'run csv stock import view...', symbol
        self.underlying = Underlying(
            symbol=symbol,
            start='2009-01-01',
            stop='2016-01-01'
        )
        self.underlying.save()

        #self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
        #self.client.get(reverse('admin:csv_option_h5x', kwargs={'symbol': symbol.lower()}))

        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/raw/contract' % symbol.lower())
        df_option = db.select('option/%s/raw/data' % symbol.lower())
        db.close()

        print 'df_contract: %d' % len(df_contract)
        print 'df_option: %d' % len(df_option)

    def test_both(self):
        """
        Test old and new import by contract and option size
        """
        print 'total symbols:', len(self.symbols)
        symbol = self.symbols[-4].lower()

        db = pd.HDFStore(QUOTE)
        df_contract0 = db.select('option/%s/raw/contract' % symbol)
        df_option0 = db.select('option/%s/raw/data' % symbol)
        db.close()
        print 'old', len(df_contract0), len(df_option0)

        db = pd.HDFStore('quote2.h5')
        df_contract1 = db.select('option/%s/raw/contract' % symbol)
        df_option1 = db.select('option/%s/raw/data' % symbol)
        db.close()
        print 'new', len(df_contract1), len(df_option1)

        if len(df_contract0) == len(df_contract1) and len(df_option0) == len(df_option1):
            print 'all same'
        else:
            diff = np.setdiff1d(
                df_contract0['option_code'],
                df_contract1['option_code']
            )
            if len(diff) == 0:
                assert len(df_contract0['option_code'].unique()) == len(df_contract1['option_code'])
                print 'contract same length, some duplicate contract in old'
            else:
                print diff

            codes1 = list(df_contract1['option_code'])
            for i, code0 in enumerate(diff):
                print i, code0,
                if code0 in codes1:
                    df0 = df_option0.query('option_code == %r' % code0)
                    df1 = df_option1.query('option_code == %r' % code0)
                    length0 = len(df0)
                    length1 = len(df1)

                    if length0 != length1:
                        print 'found but different length'
                        print length0, length1, length0 == length1
                        print df_contract0.query('option_code == %r' % code0)
                        print df0.to_string(line_width=1000)
                        print df_contract1.query('option_code == %r' % code0)
                        print df1.to_string(line_width=1000)
                        print '*' * 200
                        exit()
                else:
                    print 'not found on new'
                    print df_contract0.query('option_code == %r' % code0).to_string(line_width=1000)

                    df0 = df_option0.query('option_code == %r' % code0)
                    df1 = df_option1.query('option_code == %r' % code0)

                    print 'old got:', len(df0), 'new got:', len(df1)
                    print df0.to_string(line_width=1000)
                    print df1.to_string(line_width=1000)
                    print '*' * 200
                print ''
