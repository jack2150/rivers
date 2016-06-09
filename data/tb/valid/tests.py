import os

import pandas as pd
from base.tests import TestSetUp
from data.tb.valid.options import ValidRawOption
from rivers.settings import CLEAN_DIR, QUOTE_DIR

symbol = 'aig'
path = os.path.join(CLEAN_DIR, '__%s__.h5' % symbol.lower())
db = pd.HDFStore(path)
df_normal = db.select('option/%s/raw/normal' % symbol.lower())
df_others = db.select('option/%s/raw/others' % symbol.lower())
df_split0 = db.select('option/%s/raw/split/old' % symbol.lower())
db.close()


class TestValidRawOption(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.valid_raw = ValidRawOption(symbol)

    def test_bid_gt_ask(self):
        old_length = len(df_normal)
        print 'run bid_gt_ask...'
        df_normal1 = self.valid_raw.bid_gt_ask(df_normal)
        new_length = len(df_normal1)
        print 'old_length: %d, new_length: %d' % (old_length, new_length)
        self.assertGreaterEqual(old_length, new_length)

    def test_ask_gt_1k(self):
        old_length = len(df_normal)
        print 'run ask_gt_1k...'
        df_normal1 = self.valid_raw.ask_gt_1k(df_normal)
        new_length = len(df_normal1)
        print 'old_length: %d, new_length: %d' % (old_length, new_length)
        self.assertGreaterEqual(old_length, new_length)

    def test_bid_zero_ask_gt_one(self):
        old_length = len(df_normal)
        print 'run bid_zero_ask_gt_one...'
        df_normal1 = self.valid_raw.bid_zero_ask_gt_one(df_normal)
        new_length = len(df_normal1)
        print 'old_length: %d, new_length: %d' % (old_length, new_length)
        self.assertGreaterEqual(old_length, new_length)

    def test_valid_others(self):
        """
        Test valid all other columns
        """
        old_length = len(df_normal)
        print 'run column_lt_zero...'
        df_normal1 = self.valid_raw.column_lt_zero(df_normal)
        new_length = len(df_normal1)
        print 'old_length: %d, new_length: %d' % (old_length, new_length)
        self.assertGreaterEqual(old_length, new_length)

    def test_start(self):
        """
        Test start all raw options validation
        """
        print 'run start with df_normal...'
        self.valid_raw.start()
