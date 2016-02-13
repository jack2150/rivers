from base.utests import TestUnitSetUp
from research.algorithm.models import Formula
from research.strategy.backtest import TradeBacktest
from research.strategy.models import Trade
from research.strategy.trade.option_cask import get_price_ask
from research.strategy.trade.option_cs import get_cycle_strike, get_cycle_strike2
from research.strategy.trade.option_citm import get_prob_itm
import pandas as pd


class TestStrategy(TestUnitSetUp):
    def ready_signal(self):
        """
        Ready df_signal for trade backtest
        """
        self.formula = Formula.objects.get(rule='Ewma Chg D')
        backtest = self.formula.start_backtest()
        backtest.set_symbol_date(self.symbol, '2010-01-01', '2014-12-31')
        backtest.get_data()
        hd_args = {'span': 20, 'previous': 20}

        df_stock = backtest.handle_data(backtest.df_stock, **hd_args)
        df_signal = backtest.create_signal(df_stock)
        self.df_signal = df_signal.reset_index(drop=True)

    def ready_backtest(self):
        """
        Ready up trade backtest
        """
        self.backtest = TradeBacktest(self.symbol, self.trade)
        self.backtest.set_algorithm(
            formula=self.formula, report_id=1, df_signal=self.df_signal
        )
        self.backtest.get_data()
        self.backtest.get_extra()
        self.backtest.set_commission(1)
        self.backtest.set_capital(10000)

    def setUp(self):
        self.symbol = ''
        self.trade = Trade()


class TestStrategy2(TestUnitSetUp):
    def ready_signal(self):
        """
        Ready df_signal for trade backtest
        """
        algorithm = Formula.objects.get(rule='Ewma Chg D - H')
        backtest = algorithm.start_backtest()
        backtest.set_symbol_date(self.symbol, '2010-01-01', '2014-12-31')
        backtest.get_data()
        hd_args = {'span': 20, 'previous': 20}
        cs_args = {'holding': 20}

        df_stock = backtest.handle_data(backtest.df_stock, **hd_args)
        df_signal = backtest.create_signal(df_stock, **cs_args)
        self.df_signal = df_signal.reset_index(drop=True)

    def ready_backtest(self):
        """
        Ready up trade backtest
        """
        self.backtest = TradeBacktest(self.symbol, self.trade)
        self.backtest.set_algorithm(self.df_signal)
        self.backtest.get_data()
        self.backtest.get_extra()
        self.backtest.set_commission(1)
        self.backtest.set_capital(10000)

    def setUp(self):
        self.symbol = ''
        self.trade = Trade()


class TestGetCycleStrike(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Single CALL *CS')
        self.ready_backtest()

    def test_get_cycle_strike(self):
        """

        :return:
        """
        option0, option1 = get_cycle_strike(
            df_all=self.backtest.df_all,
            date0=self.df_signal['date0'][0],
            date1=self.df_signal['date1'][0],
            name='CALL',
            close=26.71,
            cycle=0,
            strike=0
        )

        df_code = pd.DataFrame([option0, option1])
        print df_code.to_string(line_width=1000)

    def test_get_cycle_strike2(self):
        """

        :return:
        """
        options = get_cycle_strike2(
            df_all=self.backtest.df_all,
            date0=self.df_signal['date0'][0],
            date1=self.df_signal['date1'][0],
            name='CALL',
            close=26.71,
            cycle=0,
            strike=0,
            wide=2
        )

        df_code = pd.DataFrame(list(options))
        print df_code.to_string(line_width=1000)


class TestGetProbITM(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Single CALL *CS')
        self.ready_backtest()

    def test_get_prob_itm(self):
        """

        :return:
        """
        option0, option1 = get_prob_itm(
            df_all=self.backtest.df_all,
            date0=self.df_signal['date0'][0],
            date1=self.df_signal['date1'][0],
            name='PUT',
            cycle=0,
            itm=30
        )

        df_code = pd.DataFrame([option0, option1])
        print df_code.to_string(line_width=1000)


class TestGetPriceAsk(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal()
        self.trade = Trade.objects.get(name='Single CALL *CS')
        self.ready_backtest()

    def test_get_price_ask(self):
        """

        :return:
        """
        option0, option1 = get_price_ask(
            df_all=self.backtest.df_all,
            date0=self.df_signal['date0'][0],
            date1=self.df_signal['date1'][0],
            name='PUT',
            cycle=0,
            ask=1.3
        )

        df_code = pd.DataFrame([option0, option1])
        print df_code.to_string(line_width=1000)

