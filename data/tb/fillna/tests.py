from django.core.urlresolvers import reverse
from base.tests import TestSetUp
import numpy as np
import pandas as pd

from data.models import SplitHistory
from data.tb.fillna.normal import FillNaNormal
from data.tb.fillna.split_new import FillNaSplitNew
from data.tb.fillna.split_old import FillNaSplitOld
from rivers.settings import QUOTE_DIR


class TestFillNaNormal(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'
        self.fillna_normal = FillNaNormal(self.symbol)

    def test_get_data(self):
        """
        Test get clean df_normal data from h5 db
        """
        self.fillna_normal.get_data()

        print self.fillna_normal.df_normal.head(20).to_string(line_width=1000)
        self.assertTrue(len(self.fillna_normal.close))
        self.assertTrue(len(self.fillna_normal.df_normal))
        self.assertTrue(len(self.fillna_normal.rate))
        self.assertTrue(len(self.fillna_normal.df_div))

    def test_count_missing(self):
        """
        Test count missing for each option_code
        """
        self.fillna_normal.get_data()
        self.fillna_normal.count_missing()

        print list(self.fillna_normal.df_missing.columns)
        self.assertEqual(
            list(self.fillna_normal.df_missing.columns),
            ['option_code', 'count0', 'start', 'stop', 'count1',
             'missing', 'diff', 'pct', 'fill0', 'fill1', 'fill']
        )

        self.assertTrue(len(self.fillna_normal.df_missing))

    def test_fill_missing(self):
        """
        Test fill missing row for each options
        """
        self.fillna_normal.get_data()
        self.fillna_normal.count_missing()
        print 'run fill_missing...'
        self.fillna_normal.fill_missing()

        print 'total fillna new rows: %d' % len(self.fillna_normal.df_fillna)
        self.assertTrue(len(self.fillna_normal.df_fillna))

    def test_remove_missing(self):
        """
        Test remove absence data when too many rows missing
        """
        self.fillna_normal.get_data()
        length0 = len(self.fillna_normal.df_normal)
        self.fillna_normal.count_missing()

        print 'run remove_missing...'
        self.fillna_normal.remove_missing()
        length1 = len(self.fillna_normal.df_normal)
        self.assertGreater(length0, length1)

    def test_save(self):
        """
        Test process all fillna then save into db
        """
        self.fillna_normal.save()

        db = pd.HDFStore(QUOTE_DIR)
        df_normal = db.select('option/%s/fillna/normal' % self.symbol.lower())
        db.close()

        print 'fillna df_normal: %d' % len(df_normal)
        self.assertTrue(len(df_normal))


class TestFillNaSplitNew(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'DDD'
        self.fillna_split_new = FillNaSplitNew(self.symbol)

        self.split_history = SplitHistory(
            symbol='DDD',
            date='2013-02-25',
            fraction='2/3'
        )
        self.split_history.save()

    def test_get_data(self):
        """
        Test get clean df_normal data from h5 db
        """
        self.fillna_split_new.get_data()

        for code in self.fillna_split_new.df_split1['new_code'].unique():
            df = self.fillna_split_new.df_split1.query('new_code == %r' % code)

            print df.to_string(line_width=1000)
            break

        self.assertTrue(len(self.fillna_split_new.df_stock))
        self.assertTrue(len(self.fillna_split_new.df_split1))
        self.assertTrue(len(self.fillna_split_new.df_rate))
        self.assertTrue(len(self.fillna_split_new.df_div))

    def test_count_missing(self):
        """
        Test count missing for each option_code
        """
        self.fillna_split_new.get_data()
        self.fillna_split_new.count_missing()

        print self.fillna_split_new.df_missing.head(20)
        print list(self.fillna_split_new.df_missing.columns)
        self.assertEqual(
            list(self.fillna_split_new.df_missing.columns),
            ['new_code', 'count0', 'start', 'stop', 'count1',
             'missing', 'diff', 'pct', 'fill0', 'fill1', 'fill']
        )

        self.assertTrue(len(self.fillna_split_new.df_missing))

    def test_fill_missing(self):
        """
        Test fill missing row for each options
        """
        self.fillna_split_new.get_data()
        self.fillna_split_new.count_missing()
        print 'run fill_missing...'
        self.fillna_split_new.fill_missing()

        print 'total fillna new rows: %d' % len(self.fillna_split_new.df_fillna)
        self.assertTrue(len(self.fillna_split_new.df_fillna))

    def test_save(self):
        """
        Test process all fillna then save into db
        """
        self.fillna_split_new.save()

        db = pd.HDFStore(QUOTE_DIR)
        df_split1 = db.select('option/%s/fillna/split/new' % self.symbol.lower())
        db.close()

        print 'fillna df_split/new: %d' % len(df_split1)
        self.assertTrue(len(df_split1))


class TestFillNaSplitOld(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'
        self.fillna_split_old = FillNaSplitOld(self.symbol)

        self.split_history = SplitHistory(
            symbol='AIG',
            date='2009-07-01',
            fraction='5/100'
        )
        self.split_history.save()

    def test_get_data(self):
        """
        Test get clean df_normal data from h5 db
        """
        self.fillna_split_old.get_data()

        for code in self.fillna_split_old.df_split0['option_code'].unique():
            df = self.fillna_split_old.df_split0.query('option_code == %r' % code)

            print df.to_string(line_width=1000)
            break

        self.assertTrue(len(self.fillna_split_old.df_stock))
        self.assertTrue(len(self.fillna_split_old.df_split0))
        self.assertTrue(len(self.fillna_split_old.df_rate))
        self.assertTrue(len(self.fillna_split_old.df_div))

    def test_count_missing(self):
        """
        Test count missing for each option_code
        """
        self.fillna_split_old.get_data()
        self.fillna_split_old.count_missing()

        print list(self.fillna_split_old.df_missing.columns)
        self.assertEqual(
            list(self.fillna_split_old.df_missing.columns),
            ['option_code', 'count0', 'start', 'stop', 'count1',
             'missing', 'diff', 'pct', 'fill0', 'fill1', 'fill']
        )

        self.assertTrue(len(self.fillna_split_old.df_missing))

    def test_fill_missing(self):
        """
        Test fill missing row for each options
        """
        self.fillna_split_old.get_data()
        self.fillna_split_old.count_missing()
        print 'run fill_missing...'
        self.fillna_split_old.fill_missing()

        print 'total fillna new rows: %d' % len(self.fillna_split_old.df_fillna)
        self.assertTrue(len(self.fillna_split_old.df_fillna))

    def test_save(self):
        """
        Test process all fillna then save into db
        """
        self.fillna_split_old.save()

        db = pd.HDFStore(QUOTE_DIR)
        df_split0 = db.select('option/%s/fillna/split/old' % self.symbol.lower())
        db.close()

        print 'fillna df_split/old: %d' % len(df_split0)
        self.assertTrue(len(df_split0))
