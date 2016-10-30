import os
from base.utests import TestUnitSetUp  # require
from research.strategy.models import Trade
from research.strategy.trade.tests import TestStrategy2
import pandas as pd
from rivers.settings import TEMP_DIR


class TestVerticalCS(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'VXX'
        self.ready_signal0()
        self.trade = Trade.objects.get(name='Vertical -CS')

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
                **{'name': 'call', 'side': 'follow', 'cycle': 0, 'strike': 0, 'wide': 1}
            )
            db.append(key, df_trade)
        db.close()

        return df_trade

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        # todo: previous price is wrong???
        # todo: wrong % for split date

        self.ready_backtest()
        # print self.df_signal.to_string(line_width=1000)
        self.backtest.update_signal()
        self.df_signal = self.backtest.df_signal
        # self.df_signal = self.df_signal[self.df_signal['date0'] == '2012-09-27']
        print self.df_signal.to_string(line_width=1000)
        report = []
        for side in ('follow', 'reverse', 'buy', 'sell')[2:]:
            for name in ('call', 'put'):
                kwargs = {'name': name, 'side': side, 'cycle': 0, 'strike': 0, 'wide': 2}
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

        # todo: problem in backtest

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.get_trade()

        print self.df_signal.to_string(line_width=1000)

        print len(self.backtest.df_all)
        print len(self.backtest.df_iv)

        df_list = self.backtest.join_data(
            df_trade, self.backtest.df_stock, self.backtest.df_all, self.backtest.df_iv
        )

        for df_daily in df_list:
            print df_daily.to_string(line_width=1000)
