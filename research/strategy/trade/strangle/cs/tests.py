import os
from base.utests import TestUnitSetUp  # require
from research.strategy.models import Trade
from research.strategy.trade.tests import TestStrategy2
import pandas as pd
from rivers.settings import TEMP_DIR


class TestStrangleCS(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal0()
        self.trade = Trade.objects.get(name='Strangle -CS')

    def get_trade(self):
        """
        Get df_trade from db or create new one
        """
        path = os.path.join(TEMP_DIR, 'test_strategy.h5')
        db = pd.HDFStore(path)
        key = '%s/%d/trade' % (self.symbol, self.trade.id)
        self.ready_backtest()
        self.ready_signal1()
        try:
            df_trade = db.select(key)
        except KeyError:
            df_trade = self.backtest.create_order(
                self.df_signal,
                self.backtest.df_all,
                **{'side': 'follow', 'cycle': 0, 'strike0': 0, 'strike1': 0}
            )
            db.append(key, df_trade)
        db.close()

        return df_trade

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        self.ready_backtest()
        # self.ready_signal1()
        # print self.df_signal.to_string(line_width=1000)
        report = []
        for side in ('follow', 'reverse', 'buy', 'sell')[2:]:
            for i in range(-3, 2):
                kwargs = {'side': side, 'cycle': 0, 'strike0': i, 'strike1': -i}
                print kwargs
                df_trade = self.backtest.create_order(
                    self.df_signal,
                    self.backtest.df_all,
                    **kwargs
                )
                print df_trade.to_string(line_width=500)
                print 'sum:', df_trade['pct_chg'].sum(),
                print 'profit:', len(df_trade[df_trade['pct_chg'] > 0]),
                print 'loss:', len(df_trade[df_trade['pct_chg'] < 0])
                report.append([
                    df_trade['pct_chg'].sum(),
                    len(df_trade[df_trade['pct_chg'] > 0]),
                    len(df_trade[df_trade['pct_chg'] < 0])
                ])
                print ''

        print pd.DataFrame(report, columns=['sum', 'profit', 'loss'])

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.get_trade()

        print df_trade.to_string(line_width=1000)

        print len(self.backtest.df_all)
        print len(self.backtest.df_iv)

        df_list = self.backtest.join_data(
            df_trade, self.backtest.df_stock, self.backtest.df_all, self.backtest.df_iv
        )

        for df_daily in df_list:
            print df_daily.to_string(line_width=1000)
