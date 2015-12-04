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
            'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG'
        ]

    def test_mass_csv_option_h5x(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        # self.skipTest('Only test when need!')
        print 'run mass csv option import 2...'

        for symbol in self.symbols:
            self.underlying = Underlying(
                symbol=symbol,
                start='2009-01-01',
                stop='2016-01-01'
            )
            self.underlying.save()
            self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
            self.client.get(reverse('admin:csv_option_h5x', kwargs={'symbol': symbol}))

    def test_csv_option_h5x(self):
        """
        Test csv option import into h5 db after csv stock import
        some of the csv can be wrong, for example fslr 08-25-2011 got wrong cycle info
        """
        symbol = self.symbols[0]

        # self.skipTest('Only test when need!')
        print 'run csv stock import view...'
        self.underlying = Underlying(
            symbol=symbol,
            start='2009-01-01',
            stop='2016-01-01'
        )
        self.underlying.save()

        # self.client.get(reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}))
        self.client.get(reverse('admin:csv_option_h5x', kwargs={'symbol': symbol}))

    def test123(self):
        db = pd.HDFStore('quote2.h5')
        df_contract1 = db.select('option/aig/raw/contract')
        df_option1 = db.select('option/aig/raw/data')
        db.close()
        print 'new', len(df_contract1), len(df_option1)

        # todo: AIG100220C5 AIG100220C5
        #contract = df_contract1.query('ex_month == %r & ex_year == %r & strike == %r' % (
        #    'FEB', 10, 2
        #))
        contract = df_contract1.query('option_code == %r' % (
           'AIG100220C5'
        ))

        for c in contract:
            print c
            print df_option1.query('option_code == %r' % c)

    def test_both(self):
        db = pd.HDFStore(QUOTE)
        df_contract0 = db.select('option/aig/raw/contract')
        df_option0 = db.select('option/aig/raw/data')
        db.close()
        print 'old', len(df_contract0), len(df_option0)

        db = pd.HDFStore('quote2.h5')
        df_contract1 = db.select('option/aig/raw/contract')
        df_option1 = db.select('option/aig/raw/data')
        db.close()
        print 'new', len(df_contract1), len(df_option1)

        codes0 = list(df_contract0['option_code'])
        codes1 = list(df_contract1['option_code'])

        diff = np.setdiff1d(
            df_contract0['option_code'], df_contract1['option_code']
        )

        print len(df_contract1.drop_duplicates('option_code'))

        """
        l = df_contract1['option_code'].value_counts()
        l = l[l == 2]

        for k in l.index:
            print k
            print df_option1.query('option_code == %r' % k)

            break
        """


        """
        for i, code0 in enumerate(df_contract0['option_code']):
            print i, code0,
            if code0 in codes1:
                df0 = df_option0.query('option_code == %r' % code0)
                df1 = df_option1.query('option_code == %r' % code0)
                length0 = len(df0)
                length1 = len(df1)

                if length0 != length1:
                    print 'found but different length'
                    print length0, length1, length0 == length1
                    print df0.to_string(line_width=1000)
                    print df1.to_string(line_width=1000)
                    print '*' * 200
                    exit()
            else:
                print 'not found on new'
                df0 = df_option0.query('option_code == %r' % code0)

                print len(df0)
                print df0.to_string(line_width=1000)
                print '*' * 200
                exit()
            print ''
        """












