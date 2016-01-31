import pandas as pd

from base.utests import TestUnitSetUp
from research.algorithm.models import Formula
from simulation.models import Strategy


class TestStrategyBuy(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'

        self.algorithm = Formula.objects.get(id=1)

        self.quant = self.algorithm.start_backtest()
        self.quant.seed_data(self.symbol)
        self.arguments = {'span': 20, 'previous': 20}

        self.strategy = Strategy.objects.get(name='Stock')

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.arguments)
        df_signal = self.quant.create_signal(df_stock)
        r0 = pd.Series(self.quant.report(df_stock, df_signal))

        for side in ('follow', 'buy', 'sell'):
            print 'side:', side
            df_order = self.strategy.make_order(df_stock, df_signal, side)
            print df_order.to_string(line_width=500)

            print '=' * 100


class TestStrategyStopLoss(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'

        self.algorithm = Formula.objects.get(id=1)

        self.quant = self.algorithm.start_backtest()
        self.quant.seed_data(self.symbol)
        self.arguments = {'span': 20, 'previous': 20}

        self.strategy = Strategy.objects.get(name='Stop Loss')

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.arguments)
        df_signal = self.quant.create_signal(df_stock)
        r0 = pd.Series(self.quant.report(df_stock, df_signal))

        print 'using gtc stop loss order...'
        df_order = self.strategy.make_order(df_stock, df_signal, 'gtc', 10)

        for time1 in ('open', 'during', 'close'):
            print df_order[df_order['time1'] == time1].to_string(line_width=200)
            print ''

        r1 = pd.Series(self.quant.report(df_stock, df_order))

        print 'using close only stop loss order...'
        df_order = self.strategy.make_order(df_stock, df_signal, 'close', 5)

        # print df_stop_loss.to_string(line_width=200)
        r2 = pd.Series(self.quant.report(df_stock, df_order))

        print pd.DataFrame([r0, r1, r2]).to_string(line_width=400)


class TestStrategyLimit(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'

        self.algorithm = Formula.objects.get(id=1)

        self.quant = self.algorithm.start_backtest()
        self.quant.seed_data(self.symbol)
        self.arguments = {'span': 20, 'previous': 20}

        self.strategy = Strategy.objects.get(name='Limit')

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.arguments)
        df_signal = self.quant.create_signal(df_stock)
        r0 = pd.Series(self.quant.report(df_stock, df_signal))

        print 'using gtc stop loss order...'
        df_order = self.strategy.make_order(df_stock, df_signal, 'gtc', 10)

        for time1 in ('open', 'during', 'close'):
            print df_order[df_order['time1'] == time1].to_string(line_width=200)
            print ''

        r1 = pd.Series(self.quant.report(df_stock, df_order))

        print 'using close only stop loss order...'
        df_order = self.strategy.make_order(df_stock, df_signal, 'close', 5)

        # print df_stop_loss.to_string(line_width=200)
        r2 = pd.Series(self.quant.report(df_stock, df_order))

        print pd.DataFrame([r0, r1, r2]).to_string(line_width=400)


class TestStrategyOneCancelOther(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'

        self.algorithm = Formula.objects.get(id=1)

        self.quant = self.algorithm.start_backtest()
        self.quant.seed_data(self.symbol)
        self.arguments = {'span': 60, 'previous': 20}

        self.strategy = Strategy.objects.get(name='One Cancel Other')

    def test_make_order(self):
        """
        Test trade using stop loss order
        """
        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.arguments)
        df_signal = self.quant.create_signal(df_stock)
        r0 = pd.Series(self.quant.report(df_stock, df_signal))

        print 'using gtc stop loss order...'
        df_order = self.strategy.make_order(df_stock, df_signal, 'gtc', 10, 10)

        #for order in ('stop loss', 'limit', ''):
        #    print df_order[df_order['order'] == order].to_string(line_width=200)
        #    print ''
        print df_order.to_string(line_width=200)

        r1 = pd.Series(self.quant.report(df_stock, df_order))

        print 'using close only stop loss order...'

        df_order = self.strategy.make_order(df_stock, df_signal, 'close', 10, 10)

        #for order in ('stop loss', 'limit', ''):
        #    print df_order[df_order['order'] == order].to_string(line_width=200)
        print df_order.to_string(line_width=200)


        r2 = pd.Series(self.quant.report(df_stock, df_order))

        print pd.DataFrame([r0, r1, r2]).to_string(line_width=400)
