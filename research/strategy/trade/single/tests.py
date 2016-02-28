from base.utests import TestUnitSetUp  # require
from research.strategy.models import Trade
from research.strategy.trade.single.call_cs import get_cycle_strike
from research.strategy.trade.tests import TestStrategy2
import pandas as pd


class TestSingleCallCS(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Single CALL *CS')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        for side in ('follow', 'long', 'short'):
            kwargs = {'side': side, 'cycle': 0, 'strike': 3}
            df_trade = self.backtest.create_order(
                self.df_signal,
                self.backtest.df_all,
                **kwargs
            )
            print df_trade.to_string(line_width=500)

            print df_trade['pct_chg'].sum()

            break

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_all,
            **{'side': 'follow', 'cycle': 0, 'strike': 3}
        )

        df_list = self.backtest.join_data(df_trade, self.backtest.df_all)

        for df_daily in df_list:
            print df_daily


class TestSinglePutCS(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Single PUT *CS')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        for side in ('follow', 'long', 'short'):
            kwargs = {'side': side, 'cycle': 0, 'strike': 3}
            df_trade = self.backtest.create_order(
                self.df_signal,
                self.backtest.df_all,
                **kwargs
            )
            print df_trade.to_string(line_width=500)

            print df_trade['pct_chg'].sum()

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_all,
            **{'side': 'follow', 'cycle': 0, 'strike': 0}
        )

        df_list = self.backtest.join_data(df_trade, self.backtest.df_all)

        for df_daily in df_list:
            print df_daily
