import itertools
import numpy as np
import pandas as pd
from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestMomentum(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.convert_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'NFLX'
        self.hd_args = {
            'period_span': 120,
            'skip_days': 0,
            'holding_period': 0
        }
        self.cs_args = {
            'direction': 'follow',
            'side': 'follow',
        }

        self.backtest = None
        self.algorithm_analysis('Momentum')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)

        print df_stock.to_string(line_width=200)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)

        print df_signal.to_string(line_width=200)

        print 'profit: %d' % len(df_signal[df_signal['pct_chg'] > 0])
        print 'loss: %d' % len(df_signal[df_signal['pct_chg'] < 0])
        print 'sum: %.2f%%' % (df_signal['pct_chg'].sum() * 100)

        columns = ('date0', 'date1', 'signal0', 'signal1',
                   'close0', 'close1', 'holding', 'pct_chg')

        for column in columns:
            self.assertIn(column, df_signal.columns)

    def test_full(self):
        """
        Test handle data and create signal using all parameters
        """
        spans = (60, 120)
        waits = (5, 10)
        ways = ('follow', 'long', 'short')
        sides = ('follow', 'reverse', 'buy', 'sell')
        parameters = list(itertools.product(spans, waits, ways, sides))

        report = []
        for span, wait, way, side in parameters:
            hd_args = {'period_span': span}
            cs_args = {'skip_days': wait, 'direction': way, 'side': side}

            print 'hd_args: %s, cs_args: %s' % (hd_args, cs_args)
            df_test = self.backtest.handle_data(self.backtest.df_stock, **hd_args)
            df_signal = self.backtest.create_signal(df_test, **cs_args)

            report.append({
                'hd': ' '.join([str(s) for s in hd_args.values()]),
                'cs': ' '.join([str(s) for s in cs_args.values()]),
                'profit': len(df_signal[df_signal['pct_chg'] > 0]),
                'loss': len(df_signal[df_signal['pct_chg'] < 0]),
                'sum': df_signal['pct_chg'].sum() * 100
            })

        df_report = pd.DataFrame(report)
        # .sort_values(['sum', 'profit'], ascending=False)

        print df_report
