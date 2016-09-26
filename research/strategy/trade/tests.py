import os

from base.utests import TestUnitSetUp
from research.algorithm.models import Formula
from research.strategy.backtest import TradeBacktest
from research.strategy.models import Trade
from research.strategy.trade.option_cask import get_price_ask
from research.strategy.trade.option_cs import get_cycle_strike, get_cycle_strike2
from research.strategy.trade.option_citm import get_prob_itm
from rivers.settings import TEMP_DIR
import pandas as pd


class TestStrategy(TestUnitSetUp):
    def ready_signal(self):
        """
        Ready df_signal for trade backtest (stock)
        """
        self.formula = Formula.objects.get(rule='Momentum')
        backtest = self.formula.start_backtest()
        backtest.set_symbol_date(self.symbol, '2010-01-01', '2015-12-31')
        backtest.get_data()
        hd_args = {
            'period_span': 120,
            'skip_days': 0,
            'holding_period': 0
        }
        cs_args = {
            'direction': 'follow',
            'side': 'follow',
        }

        df_stock = backtest.handle_data(backtest.df_stock, **hd_args)
        df_signal = backtest.create_signal(df_stock, **cs_args)
        self.df_signal = df_signal.reset_index(drop=True)

    def ready_backtest(self):
        """
        Ready up trade backtest
        """
        self.backtest = TradeBacktest(self.symbol, self.trade)
        self.backtest.set_algorithm(
            formula_id=self.formula.id, report_id=1, df_signal=self.df_signal
        )
        self.backtest.get_data()
        self.backtest.get_extra()
        self.backtest.set_commission(1)
        self.backtest.set_capital(10000)

    def setUp(self):
        self.symbol = ''
        self.trade = Trade()


class TestStrategy2(TestUnitSetUp):
    def ready_signal0(self):
        """
        Ready df_signal for trade backtest (option)
        """
        self.formula = Formula.objects.get(rule='Day to Expire')
        path = os.path.join(TEMP_DIR, 'test_strategy.h5')
        db = pd.HDFStore(path)
        try:
            self.df_signal = db.select(
                '%s/%s/signal' % (self.symbol, self.formula.id)
            ).reset_index(drop=True)
        except KeyError:
            backtest = self.formula.start_backtest()
            backtest.set_symbol_date(self.symbol, '2010-01-01', '2016-06-30')
            backtest.get_data()
            backtest.extra_data()
            hd_args = {}
            cs_args = {
                'dte': 25,
                'side': 'buy',
                'special': 'standard'
            }

            df_hd = backtest.handle_data(backtest.df_stock, **hd_args)
            df_signal = backtest.create_signal(df_hd, backtest.df_all, **cs_args)
            self.df_signal = df_signal.reset_index(drop=True)
            db.append('%s/signal' % self.symbol, self.df_signal)
        db.close()

    def ready_signal1(self):
        """
        Ready df_signal for trade backtest (option)
        """
        self.formula = Formula.objects.get(rule='Momentum')
        path = os.path.join(TEMP_DIR, 'test_strategy.h5')
        db = pd.HDFStore(path)
        try:
            self.df_signal = db.select(
                '%s/%s/signal' % (self.symbol, self.formula.id)
            ).reset_index(drop=True)
        except KeyError:
            backtest = self.formula.start_backtest()
            backtest.set_symbol_date(self.symbol, '2010-01-01', '2015-12-31')
            backtest.get_data()
            hd_args = {
                'period_span': 60,
                'skip_days': 5,
                'holding_period': 0
            }
            cs_args = {
                'direction': 'follow',
                'side': 'follow',
            }

            df_stock = backtest.handle_data(backtest.df_stock, **hd_args)
            df_signal = backtest.create_signal(df_stock, **cs_args)
            self.df_signal = df_signal.reset_index(drop=True)
        db.close()

    def ready_backtest(self):
        """
        Ready up trade backtest
        """
        self.backtest = TradeBacktest(self.symbol, self.trade)
        self.backtest.set_algorithm(
            formula_id=self.formula.id, report_id=1, df_signal=self.df_signal
        )
        self.backtest.get_data()
        self.backtest.get_extra()
        self.backtest.set_option_price()
        self.backtest.set_commission(1)
        self.backtest.set_capital(10000)

    def setUp(self):
        self.symbol = ''
        self.trade = Trade()


class TestGetCycleStrike(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal0()
        self.trade = Trade.objects.get(name='Single -CS')
        self.ready_backtest()

    def test_get_cycle_strike(self):
        """

        :return:
        """
        index = 49
        for name in ('CALL', 'PUT')[:1]:
            for price in (0, -0.4)[:1]:
                close = self.df_signal['close0'][index] + price
                date0 = self.df_signal['date0'][index]
                date1 = self.df_signal['date1'][index]
                print 'date0: %s, date1: %s, close: %.2f' % (
                    date0.strftime('%Y-%m-%d'), date1.strftime('%Y-%m-%d'), close
                )
                option0, option1 = get_cycle_strike(
                    df_all=self.backtest.df_all,
                    date0=date0,
                    date1=date1,
                    name=name,
                    close=close,
                    cycle=0,
                    strike=0
                )

                df_code = pd.DataFrame([option0, option1])
                print df_code.to_string(line_width=1000)

    def test_get_cycle_strike2(self):
        """

        :return:
        """
        for i in range(-2, 3):
            print i
            options0 = get_cycle_strike2(
                df_all=self.backtest.df_all,
                date0=self.df_signal['date0'][0],
                date1=self.df_signal['date1'][0],

                name0='CALL',
                close0=26.71,
                cycle0=0,
                strike0=i,

                name1='PUT',
                close1=26.71,
                cycle1=0,
                strike1=i,
            )
            options1 = get_cycle_strike2(
                df_all=self.backtest.df_all,
                date0=self.df_signal['date0'][0],
                date1=self.df_signal['date1'][0],

                name0='PUT',
                close0=26.71,
                cycle0=0,
                strike0=i,

                name1='CALL',
                close1=26.71,
                cycle1=0,
                strike1=i,
            )

            df_code = pd.DataFrame(list(options0) + list(options1))
            print df_code.to_string(line_width=1000)


class TestGetProbITM(TestStrategy2):
    def setUp(self):
        TestStrategy2.setUp(self)

        self.symbol = 'AIG'
        self.ready_signal0()
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
        self.ready_signal0()
        self.trade = Trade.objects.get(name='Single -CS')
        self.ready_backtest()

    def test_get_price_ask(self):
        """

        :return:
        """
        for name in ('CALL', 'PUT'):
            option0, option1 = get_price_ask(
                df_all=self.backtest.df_all,
                date0=self.df_signal['date0'][0],
                date1=self.df_signal['date1'][0],
                name=name,
                cycle=0,
                ask=1.3
            )

            df_code = pd.DataFrame([option0, option1])
            print df_code.to_string(line_width=1000)
