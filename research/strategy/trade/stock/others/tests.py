from base.utests import TestUnitSetUp  # require
from research.strategy.models import Trade
from research.strategy.trade.tests import TestStrategy


# todo: long, lose add more, short, lose, reverse
# todo: short to long is good result
# todo: long to short is bad, long should be double up


class TestStrategyOCOConvert(TestStrategy):
    def setUp(self):
        TestStrategy.setUp(self)

        # aig, bac, fslr, bidu
        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='OCO Convert')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        self.df_signal = self.df_signal[self.df_signal['holding'].apply(lambda x: x.days >= 10)]
        # print self.df_signal
        # print self.backtest.df_stock

        for side in ('follow', 'reverse', 'buy', 'sell'):
            print 'side:', side
            kwargs = {
                'side': side,
                'profit_pct0': 10, 'loss_pct0': 8,
                'profit_pct1': 10, 'loss_pct1': 8
            }
            df_trade = self.backtest.create_order(
                self.df_signal, self.backtest.df_stock, **kwargs
            )

            print df_trade.to_string(line_width=500)
            print '-' * 70
            print 'sum:', df_trade['pct_chg'].sum(),
            print 'profit:', len(df_trade[df_trade['pct_chg'] > 0]),
            print 'loss:', len(df_trade[df_trade['pct_chg'] < 0])

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_stock,
            **{'side': 'follow', 'profit_pct': 5, 'loss_pct': 5}
        )

        df_list = self.backtest.join_data(df_trade, self.backtest.df_stock)

        for df_daily in df_list:
            print df_daily


class TestStrategyOCOLossAdd(TestStrategy):
    def setUp(self):
        TestStrategy.setUp(self)

        # aig, bac, fslr, bidu
        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='OCO Loss Add')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using oco order
        """
        self.df_signal = self.df_signal[self.df_signal['holding'].apply(lambda x: x.days >= 10)]
        # print self.df_signal
        # print self.backtest.df_stock

        for side in ('follow', 'reverse', 'buy', 'sell'):
            print 'side:', side
            kwargs = {
                'side': side,
                'profit_pct0': 10, 'loss_pct0': 8,
                'profit_pct1': 10, 'loss_pct1': 8
            }
            df_trade = self.backtest.create_order(
                self.df_signal, self.backtest.df_stock, **kwargs
            )

            print df_trade.to_string(line_width=500)
            print '-' * 70
            print 'sum:', df_trade['pct_chg'].sum(),
            print 'profit:', len(df_trade[df_trade['pct_chg'] > 0]),
            print 'loss:', len(df_trade[df_trade['pct_chg'] < 0])

    def test_join_data(self):
        """
        Test join df_trade data into daily data
        """
        df_trade = self.backtest.create_order(
            self.df_signal,
            self.backtest.df_stock,
            **{'side': 'follow', 'profit_pct': 5, 'loss_pct': 5}
        )

        df_list = self.backtest.join_data(df_trade, self.backtest.df_stock)

        for df_daily in df_list:
            print df_daily