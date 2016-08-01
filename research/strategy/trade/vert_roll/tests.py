import os
from itertools import product

from base.ufunc import ts
from base.utests import TestUnitSetUp  # require
from research.strategy.models import Trade
from research.strategy.trade.tests import TestStrategy2
import pandas as pd
import numpy as np
from rivers.settings import TEMP_DIR


class TestVerticalRoll(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal0()
        self.trade = Trade.objects.get(name='Vertical Roll')

        self.args = {
            'name': 'PUT',
            'side': 'BUY',
            'safe': False,
            'dte0': 20,
            'dte1': 60,
            'distance': 20,
            'wide': 20
        }

    def get_trade(self):
        """
        Get df_trade from db or create new one
        """
        path = os.path.join(TEMP_DIR, 'test_strategy.h5')
        db = pd.HDFStore(path)
        key = '%s/%d/trade' % (self.symbol, self.trade.id)
        self.ready_backtest()
        try:
            df_trade = db.select(key)
        except KeyError:
            df_trade = self.backtest.create_order(
                self.df_signal,
                self.backtest.df_stock,
                self.backtest.df_all,
                **self.args
            )
            db.append(key, df_trade)
        db.close()

        return df_trade

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        self.ready_backtest()
        # ts(self.backtest.df_signal)

        # df_date = df_all[df_all['date'] == '2010-11-01'].sort_values('dte')
        # print df_date.to_string(line_width=1000)

        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_stock,
            self.backtest.df_all,
            **self.args
        )

        print df_trade.to_string(line_width=500)

        print 'profit:', len(df_trade[df_trade['pct_chg'] > 0])
        print 'loss:', len(df_trade[df_trade['pct_chg'] < 0])
        print df_trade['pct_chg'].sum()
        print df_trade['net_chg'].sum()

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.get_trade()

        df_list = self.backtest.join_data(
            df_trade[:2], self.backtest.df_stock, self.backtest.df_all, self.backtest.df_iv
        )

        for df_daily in df_list:
            print df_daily.to_string(line_width=1000)
