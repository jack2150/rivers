from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.tb.raw.stocks import extract_stock
from options import *
import numpy as np
import pandas as pd

# aig for old others/split, ddd for new split, bxp for special dividend
from rivers.settings import QUOTE_DIR, DB_DIR

symbols = [
    'NFLX', 'GOOG', 'AIG', 'FSLR', 'DDD', 'BP', 'C', 'CELG',
    'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG',
    'DAL', 'DIS', 'EA', 'EBAY', 'FB', 'BXP'
]


class TestExtractStock(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)
        self.symbol = 'YUM'

    def test_extract_stock(self):
        """
        Test extract stock for specific file
        """
        underlying = Underlying(
            symbol=self.symbol,
            start_date='2010-01-01',
            stop_date='2016-06-30'
        )
        underlying.save()
        extract_stock(self.symbol)


class TestExtractOption(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.path = os.path.join(DB_DIR, 'temp', 'test.h5')
        self.symbol = symbols[1]

    def create_test_h5(self, symbol):
        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        db = pd.HDFStore(path)
        self.df_stock = db.select('stock/thinkback')
        print 'df_stock: %d' % len(self.df_stock)
        db.close()

        path = os.path.join(CLEAN_DIR, 'test_%s.h5' % symbol.lower())

        if os.path.isfile(path):
            db = pd.HDFStore(path)

            self.data = {}

            names = [
                'df_all',
                'df_normal0', 'df_split0', 'df_others0',
                'df_split1', 'df_others1',
                'df_normal1',
            ]
            keys = [
                'option/raw/normal',
                'state0/normal', 'state0/split0', 'state0/others0',
                'state1/split1', 'state1/others1',
                'state2/normal'
            ]

            for name, key in zip(names, keys):
                try:
                    self.data[name] = db.select(key)
                except KeyError:
                    pass

            db.close()
        else:
            db = pd.HDFStore(path)
            raw_option = RawOption(symbol, self.df_stock)

            # state 0
            raw_option.get_data()
            raw_option.group_data()
            db.append('state0/normal', raw_option.df_normal)
            db.append('state0/split0', raw_option.df_split0)
            db.append('state0/others0', raw_option.df_others0)

            # state 1
            raw_option.get_old_split_data()
            raw_option.get_others_data()
            db.append('state1/normal', raw_option.df_normal)
            db.append('state1/split1', raw_option.df_split1)
            db.append('state1/others1', raw_option.df_others1)

            # state 2
            raw_option.continue_split_others()
            db.append('state2/normal', raw_option.df_normal)
            db.append('state2/split1', raw_option.df_split1)
            db.append('state2/others1', raw_option.df_others1)

            # state 3
            raw_option.merge_new_split_data()
            db.append('state3/normal', raw_option.df_normal)
            db.append('state3/split2', raw_option.df_split2)

            # state 4
            raw_option.format_normal_code()
            db.append('option/raw/normal', raw_option.df_normal)
            db.append('option/raw/split1', raw_option.df_split1)
            db.append('option/raw/split2', raw_option.df_split2)
            db.append('option/raw/others', raw_option.df_others1)

            db.close()

    def test_create_test_h5_2(self):
        """
        Test ready for test
        """
        self.create_test_h5(self.symbol)

    def test_get_data(self):
        """
        Test get option data only from
        """
        self.create_test_h5(self.symbol)
        self.eo = RawOption(self.symbol, self.df_stock[:20])

        print 'run get_data...'
        self.eo.get_data()

        print 'df_all length: %d' % len(self.eo.df_all)
        print self.eo.df_all[:20].to_string(line_width=1000)
        self.assertTrue(len(self.eo.df_all))

    def test_group_data(self):
        """
        Test group data for df_all into normal, split, others
        """
        self.create_test_h5(self.symbol)
        self.eo = RawOption(self.symbol, self.df_stock)

        self.eo.df_all = self.df_all

        print 'run group_data...'
        self.eo.group_data()

        self.assertTrue(len(self.eo.df_normal))
        self.assertTrue(len(self.eo.df_split0))
        self.assertTrue(len(self.eo.df_others0))

    def test_merge_split_data(self):
        """
        Test merge all split option data into df_split
        """
        self.create_test_h5(self.symbol)
        self.eo = RawOption(self.symbol, self.df_stock)

        self.eo.df_split0 = self.df_split0
        print 'run merge_split_data...'
        self.eo.get_old_split_data()

        print 'df_split0 length: %d' % (len(self.df_split0['option_code']))
        print 'df_split0 option_code: %d' % (len(self.df_split0['option_code'].unique()))
        print 'df_split1 length: %d' % (len(self.eo.df_split1['option_code']))
        print 'df_split1 option_code: %d' % (len(self.eo.df_split1['option_code'].unique()))
        self.assertNotEqual(
            len(self.df_split0['option_code'].unique()),
            len(self.eo.df_split1['option_code'].unique())
        )

    def test_merge_others_data(self):
        """
        Test merge others option data int df_others
        """
        self.create_test_h5(self.symbol)
        self.eo = RawOption(self.symbol, self.df_stock)

        df_others0 = self.data['df_others0']
        self.eo.df_others0 = df_others0
        print 'run merge_others_data...'
        self.eo.get_others_data()

        print 'df_others0 length: %d' % (len(df_others0['option_code']))
        print 'df_others0 option_code: %d' % (len(df_others0['option_code'].unique()))
        print 'df_others1 length: %d' % (len(self.eo.df_others1['option_code']))
        print 'df_others1 option_code: %d' % (len(self.eo.df_others1['option_code'].unique()))
        self.assertEqual(len(df_others0), len(self.eo.df_others1))

    def test_continue_split_others(self):
        """
        Test continue split and other row using
        """
        self.create_test_h5(self.symbol)
        self.eo = RawOption(self.symbol, self.df_stock)

        self.eo.df_normal = self.data['df_normal0']

        if 'df_split1' in self.data.keys():
            self.eo.df_split1 = self.data['df_split1']

        if 'df_others1' in self.data.keys():
            print 'here'
            self.eo.df_others1 = self.data['df_others1']

        self.eo.continue_split_others()

    def test_merge_new_split_data(self):
        """
        Test DDD with merge new split data
        cleaning using another method
        """
        self.symbol = 'DDD'
        self.create_test_h5(self.symbol)
        self.eo = RawOption(self.symbol, self.df_stock)
        self.eo.df_normal = self.df_normal1

        self.split_history = SplitHistory(
            symbol='DDD',
            date='2013-02-25',
            fraction='2/3'
        )
        self.split_history.save()

        print 'run merge_normal_event...'
        self.eo.merge_new_split_data()

    def test_format_normal_code(self):
        """
        Test format df_normal option_code
        """

        self.create_test_h5(self.symbol)
        self.eo = RawOption(self.symbol, self.df_stock)
        self.eo.df_normal = self.df_normal1

        print 'run format_normal_code...'
        self.eo.format_normal_code()

        codes = pd.Series(self.eo.df_normal['option_code'].unique())
        min_length = len(self.symbol) + 6 + 1 + 1
        too_short = codes.apply(lambda c: len(c) < min_length)
        no_symbol = codes.apply(lambda c: self.symbol.upper() not in c)

        self.assertFalse(np.count_nonzero(too_short))
        self.assertFalse(np.count_nonzero(no_symbol))

    def test_start(self):
        """
        Test start all methods for extract option data
        """
        for symbol in symbols[:1]:
            print 'using symbol: %s' % symbol
            underlying = Underlying(
                symbol=symbol,
                start_date='2009-01-01',
                stop_date='2016-01-01'
            )
            underlying.save()
            symbol = symbol.lower()

            # self.client.get(reverse('admin:raw_stock_h5', kwargs={'symbol': symbol}))

            db = pd.HDFStore(QUOTE_DIR)
            df_stock = db.select('stock/thinkback/%s' % symbol.lower())
            db.close()

            extract_option = RawOption(symbol, df_stock)
            extract_option.start()

    def test_one_day(self):
        """
        Test import 1 day of stock and options
        """
        self.symbol = 'EBAY'
        underlying = Underlying(
            symbol=self.symbol,
            start_date='2009-01-01',
            stop_date='2016-01-01'
        )
        underlying.save()

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_stock = db.select('stock/thinkback')
        db.close()

        date = '2016-03-31'
        df_stock = df_stock[date:]

        extract_option = RawOption(self.symbol, df_stock)
        extract_option.start()

        """
        print extract_option.df_normal.query('option_code == %r' % 'AIG110122C40')

        path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_option = db.select('option/raw/normal')
        db.close()

        df_temp = df_option.query('date == %r & name == "CALL"' % date)
        print df_temp.to_string(line_width=1000)
        """

    def test_parts(self):
        """

        :return:
        """
        self.symbol = 'TZA'
        underlying = Underlying(
            symbol=self.symbol,
            start_date='2009-01-01',
            stop_date='2016-01-01'
        )
        underlying.save()

        path = os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_stock = db.select('stock/thinkback')
        db.close()
        # test date: 2013-01-18
        #  df_stock = df_stock[:'2013-01-18']

        path = os.path.join(CLEAN_DIR, 'test_%s.h5' % self.symbol.lower())
        extract_option = RawOption(self.symbol, df_stock)
        """
        extract_option.get_data()
        extract_option.group_data()
        extract_option.get_old_split_data()
        extract_option.get_others_data()

        db = pd.HDFStore(path)
        db['df_normal'] = extract_option.df_normal
        db['df_split1'] = extract_option.df_split1
        db['df_others1'] = extract_option.df_others1
        db.close()
        """
        path = os.path.join(CLEAN_DIR, 'test_%s.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        extract_option.df_normal = db['df_normal']
        extract_option.df_split1 = db['df_split1']
        extract_option.df_others1 = db['df_others1']
        db.close()

        extract_option.continue_split_others()
        # extract_option.merge_new_split_data()
        # extract_option.format_normal_code()


class TestRawViews(TestSetUp):
    def test_raw_stock_h5(self):
        """
        Test raw stock import for cli
        """
        symbol = 'NFLX'.lower()
        self.client.get(reverse('admin:raw_stock_h5', kwargs={'symbol': symbol}))

        raw_input("Press ENTER to show df_stock...")

        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol)
        db = pd.HDFStore(path)
        df_stock = db.select('stock/thinkback')
        db.close()

        print df_stock.to_string(line_width=1000)

    def test_raw_option_h5(self):
        """
        Test raw option import for cli
        """
        self.client.get(reverse('admin:raw_option_h5', kwargs={'symbol': 'aig'}))