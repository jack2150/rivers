import numpy as np
import pandas as pd
from base.tests import TestSetUp
from data.tb.revalid.options import ValidCleanOption, check_round, option_round
from rivers.settings import CLEAN, QUOTE

symbol = 'aig'
db = pd.HDFStore(CLEAN)
df_normal = db.select('option/%s/clean/normal' % symbol.lower())
df_split0 = db.select('option/%s/clean/split/old' % symbol.lower())
db.close()


class TestRoundClass(TestSetUp):
    def test_check_round(self):
        """
        Test check options bid ask round
        """
        data = [3.9, 7.35, 11.85, 25.35]
        name = check_round(data)
        self.assertEqual(name, '05')
        print 'data: %s, result: %s' % (data, name)

        data = [3.9, 7.3, 11.8, 25.3]
        name = check_round(data)
        self.assertEqual(name, '10')
        print 'data: %s, result: %s' % (data, name)

        data = [3.92, 7.38, 11.85, 25.31]
        name = check_round(data)
        self.assertEqual(name, '01')
        print 'data: %s, result: %s' % (data, name)

    def test_correct_round(self):
        """
        Test option bid/ask value into correct round
        """
        value = 9.33
        name = 'ask'
        result = option_round(value, name, '01')
        self.assertEqual(result, value)
        print 'method: 01, name: %s, value: %s, result: %s' % (name, value, result)

        value = 9.33
        result = option_round(value, name, '10')
        self.assertEqual(result, 9.4)
        print 'method: 10, name: %s, value: %s, result: %s' % (name, value, result)

        value = 9.31
        result = option_round(value, name, '05')
        self.assertEqual(result, 9.35)
        print 'method: 05, name: %s, value: %s, result: %s' % (name, value, result)

        value = 9.39
        result = option_round(value, name, '05')
        self.assertEqual(result, 9.4)
        print 'method: 05, name: %s, value: %s, result: %s' % (name, value, result)

        value = 9.31
        name = 'bid'
        result = option_round(value, name, '05')
        self.assertEqual(result, 9.3)
        print 'method: 05, name: %s, value: %s, result: %s' % (name, value, result)

        value = 9.39
        result = option_round(value, name, '05')
        self.assertEqual(result, 9.35)
        print 'method: 05, name: %s, value: %s, result: %s' % (name, value, result)


class TestValidCleanOption(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.valid_clean = ValidCleanOption(symbol)

    def test_mark_gt_ask(self):
        """
        Test mark is greater than ask price
        """
        length0 = len(df_normal)
        print 'df_normal length: %d' % length0
        print 'run mark_gt_ask...'
        print '-' * 70
        df_result = self.valid_clean.mark_gt_ask(df_normal.copy())
        print 'df_result length: %d' % len(df_result)

        self.assertGreaterEqual(length0, len(df_result))

    def test_theo_zero_bid_ask(self):
        """
        Test theory price zero and bid-ask also zero, update into 0.01
        """
        length0 = len(df_normal)
        print 'df_normal length: %d' % length0
        print 'run theo_zero_bid_ask...'
        print '-' * 70
        df_result = self.valid_clean.theo_zero_bid_ask(df_normal)
        print 'df_result length: %d' % len(df_result)

    def test_theo_gt_bid_ask_zero(self):
        """
        Test theory price is greater than zero bid-ask
        """
        length0 = len(df_normal)
        print 'df_normal length: %d' % length0
        print 'run theo_gt_bid_ask_zero...'
        print '-' * 70
        df_result = self.valid_clean.theo_gt_bid_ask_zero(df_normal)
        print 'df_result length: %d' % len(df_result)

    def test_valid(self):
        """
        Test re-valid cleaned data
        """
        len0 = len(df_normal)
        len1 = len(df_split0)
        print 'df_normal length: %d' % len0
        print 'df_split0 length: %d' % len1
        self.valid_clean.df_list = {
            'normal': df_normal.copy(),
            'split0': df_split0.copy()
        }

        print 'start re-valid clean data...'
        self.valid_clean.valid()

        print 'df_normal length: %d' % len(self.valid_clean.df_list['normal'])
        print 'df_split0 length: %d' % len(self.valid_clean.df_list['split0'])
        self.assertGreaterEqual(len0, len(self.valid_clean.df_list['normal']))
        self.assertGreaterEqual(len1, len(self.valid_clean.df_list['split0']))

    def test_start(self):
        """
        Test re-valid clean options data
        """
        self.valid_clean.start()

