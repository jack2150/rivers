from django.core.urlresolvers import reverse
from base.tests import TestSetUp
from data.tb.raw.stocks import extract_stock
from options import *
import numpy as np
import pandas as pd

# aig for old others/split, ddd for new split, bxp for special dividend
symbols = [
    'AIG', 'FSLR', 'SNDK', 'DDD', 'BP', 'C', 'CELG',
    'YUM', 'XOM', 'WMT', 'WFC', 'VZ', 'TWTR', 'TSLA', 'PG',
    'DAL', 'DIS', 'EA', 'EBAY', 'FB', 'BXP'
]


class TestExtractOption(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = symbols[0]

    def create_test_h5(self, symbol):
        # noinspection PyUnresolvedReferences
        path = os.path.join(BASE_DIR, 'data', 'tb', 'raw', 'test.h5')
        # if False:
        if os.path.isfile(path):
            db = pd.HDFStore(path)
            self.df_stock = db.select('stock/thinkback/%s' % symbol.lower())
            self.df_all = db.select('option/%s/raw/all' % symbol.lower())
            self.df_normal0 = pd.DataFrame()
            self.df_normal1 = pd.DataFrame()
            self.df_split0 = pd.DataFrame()
            self.df_split1 = pd.DataFrame()
            self.df_others0 = pd.DataFrame()
            self.df_others1 = pd.DataFrame()

            keys = [('df_split0', 'raw/split'), ('df_others0', 'raw/others'),
                    ('df_split1', 'merge/split'), ('df_others1', 'merge/others'),
                    ('df_normal0', 'raw/split'), ('df_normal1', 'merge/normal')]
            for var, key in keys:
                try:
                    setattr(
                        self, var,
                        db.select('option/%s/%s' % (symbol.lower(), key))
                    )
                except KeyError:
                    pass
            db.close()
        else:
            # get df_stock from quote if exists, if not create it
            db = pd.HDFStore(QUOTE)
            try:
                self.df_stock = db.select('stock/thinkback/%s' % symbol.lower())
            except KeyError:
                print 'df_stock not found, inserting...'
                self.client.get(reverse('admin:raw_stock_h5', kwargs={'symbol': symbol}))
                self.df_stock = db.select('stock/thinkback/%s' % symbol.lower())
                print 'done insert df_stock'
            db.close()

            # save df_stock into test.h5
            db = pd.HDFStore(path)
            db.append('stock/thinkback/%s' % symbol.lower(), self.df_stock)

            # create then save df_all
            extract_option = ExtractOption(symbol, self.df_stock)
            extract_option.get_data()
            self.df_all = extract_option.df_all
            db.append('option/%s/raw/all' % symbol.lower(), self.df_all)

            # create then save df_normal, df_split, df_others
            extract_option.group_data()
            self.df_normal0 = extract_option.df_normal
            self.df_split0 = extract_option.df_split0
            self.df_others0 = extract_option.df_others0
            db.append('option/%s/raw/normal' % symbol.lower(), self.df_normal0)
            db.append('option/%s/raw/split' % symbol.lower(), self.df_split0)
            db.append('option/%s/raw/others' % symbol.lower(), self.df_others0)

            extract_option.merge_old_split_data()
            extract_option.merge_others_data()

            self.df_split1 = extract_option.df_split1
            self.df_others1 = extract_option.df_others1
            db.append('option/%s/merge/split' % symbol.lower(), self.df_split1)
            db.append('option/%s/merge/others' % symbol.lower(), self.df_others1)

            extract_option.continue_split_others()
            self.df_normal1 = extract_option.df_normal
            db.append('option/%s/merge/normal' % symbol.lower(), self.df_normal1)

            db.close()

    def test_get_data(self):
        """
        Test get option data only from
        """
        self.create_test_h5(self.symbol)
        self.eo = ExtractOption(self.symbol, self.df_stock)

        print 'run get_data...'
        self.eo.get_data()

        print 'df_all length: %d' % len(self.eo.df_all)
        self.assertTrue(len(self.eo.df_all))

    def test_group_data(self):
        """
        Test group data for df_all into normal, split, others
        """
        self.create_test_h5(self.symbol)
        self.eo = ExtractOption(self.symbol, self.df_stock)

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
        self.eo = ExtractOption(self.symbol, self.df_stock)

        self.eo.df_split0 = self.df_split0
        print 'run merge_split_data...'
        self.eo.merge_old_split_data()

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
        self.eo = ExtractOption(self.symbol, self.df_stock)

        self.eo.df_others0 = self.df_others0
        print 'run merge_others_data...'
        self.eo.merge_others_data()

        print 'df_others0 length: %d' % (len(self.df_others0['option_code']))
        print 'df_others0 option_code: %d' % (len(self.df_others0['option_code'].unique()))
        print 'df_others1 length: %d' % (len(self.eo.df_others1['option_code']))
        print 'df_others1 option_code: %d' % (len(self.eo.df_others1['option_code'].unique()))
        self.assertEqual(len(self.df_others0), len(self.eo.df_others1))

    def test_continue_split_others(self):
        """
        Test continue split and other row using
        """
        self.create_test_h5(self.symbol)
        self.eo = ExtractOption(self.symbol, self.df_stock)

        self.eo.df_normal = self.df_normal0
        self.eo.df_split1 = self.df_split1
        self.eo.df_others1 = self.df_others1
        self.eo.continue_split_others()

    def test_merge_new_split_data(self):
        """
        Test DDD with merge new split data
        cleaning using another method
        """
        self.symbol = 'DDD'
        self.create_test_h5(self.symbol)
        self.eo = ExtractOption(self.symbol, self.df_stock)
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
        self.eo = ExtractOption(self.symbol, self.df_stock)
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
                start='2009-01-01',
                stop='2016-01-01'
            )
            underlying.save()
            symbol = symbol.lower()

            self.client.get(reverse('admin:raw_stock_h5', kwargs={'symbol': symbol}))

            db = pd.HDFStore(QUOTE)
            df_stock = db.select('stock/thinkback/%s' % symbol.lower())
            db.close()

            extract_option = ExtractOption(symbol, df_stock)
            extract_option.start()


class TestRawViews(TestSetUp):
    def test_raw_stock_h5(self):
        """
        Test raw stock import for cli
        """
        self.client.get(reverse('admin:raw_stock_h5', kwargs={'symbol': 'aig'}))

    def test_raw_option_h5(self):
        """
        Test raw option import for cli
        """
        self.client.get(reverse('admin:raw_option_h5', kwargs={'symbol': 'aig'}))








