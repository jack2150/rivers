from base.utests import TestUnitSetUp  # require
from research.strategy.models import Trade
from research.strategy.trade.tests import TestStrategy


class TestStrategyBuy(TestStrategy):
    def setUp(self):
        TestStrategy.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Stock')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        for side in ('follow', 'reverse', 'buy', 'sell'):
            print 'side:', side
            kwargs = {'side': side}
            df_trade = self.backtest.create_order(
                self.df_signal, **kwargs
            )
            print df_trade.to_string(line_width=500)

            print '=' * 100


class TestStrategyStopLoss(TestStrategy):
    def setUp(self):
        TestStrategy.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Stop Loss')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        for side in ('follow', 'reverse', 'buy', 'sell'):
            print 'side:', side
            kwargs = {'side': side, 'percent': 5}
            df_trade = self.backtest.create_order(
                self.df_signal, self.backtest.df_stock, **kwargs
            )
            print df_trade.to_string(line_width=500)
            print '=' * 100


class TestStrategyLimit(TestStrategy):
    def setUp(self):
        TestStrategy.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Limit')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        kwargs = {'percent': 5}
        df_trade = self.backtest.create_order(
            self.df_signal, self.backtest.df_stock, **kwargs
        )
        print df_trade.to_string(line_width=500)


class TestStrategyOCO(TestStrategy):
    def setUp(self):
        TestStrategy.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='OCO')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        kwargs = {'profit_pct': 10, 'loss_pct': 5}
        df_trade = self.backtest.create_order(
            self.df_signal, self.backtest.df_stock, **kwargs
        )
        print df_trade.to_string(line_width=500)


class TestStrategyTrailingStop(TestStrategy):
    def setUp(self):
        TestStrategy.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Trailing Stop')
        self.ready_backtest()

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        kwargs = {'percent': 10}
        df_trade = self.backtest.create_order(
            self.df_signal, self.backtest.df_stock, **kwargs
        )
        print df_trade.to_string(line_width=500)
        print df_trade['pct_chg'].sum()






