import os
import numpy as np
import pandas as pd
from base.utests import TestUnitSetUp
from research.algorithm.models import Formula
from research.strategy.backtest import TradeBacktest
from research.strategy.models import Trade, Commission
from research.strategy.views import StrategyAnalysisForm2
from rivers.settings import RESEARCH


class TestStrategyBacktest(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.formula = Formula.objects.get(rule='Ewma Chg D')

        db = pd.HDFStore(os.path.join(RESEARCH, self.symbol.lower(), 'algorithm.h5'))
        df_report = db.select('report', where='formula == %r' % self.formula.path)
        self.report = df_report.iloc[0]
        self.df_signal = db.select('signal', where='formula == %r & hd == %r & cs == %r' % (
            self.report['formula'], self.report['hd'], self.report['cs']
        ))
        db.close()

        print self.formula, self.formula.id

        self.commission = Commission.objects.get(id=1)
        self.capital = 10000

        self.trade = Trade.objects.get(name='Stop Loss')
        self.backtest = TradeBacktest(self.symbol, self.trade)
        self.backtest.set_algorithm(self.formula, self.report.name, self.df_signal)
        self.backtest.set_commission(self.commission)
        self.backtest.set_capital(self.capital)

    def test_set_args(self):
        """
        Test set arguments that ready for strategy test,
        support str list, float list, int list
        """
        print 'formula: %s' % self.formula
        print 'arguments: %s' % self.trade.get_args()
        self.backtest.set_args({
            'side': 'follow,reverse,buy,sell',
            'percent': '0:10:5'
            # 'percent': '0.0:2.5:0.5'
        })
        # self.assertEqual(len(self.backtest.args), 12)

        for arg in self.backtest.args:
            print arg
            self.assertEqual(type(arg), dict)
            self.assertEqual(len(arg), 2)
            self.assertIn(arg['side'], ('follow', 'reverse', 'buy', 'sell'))

    def test_get_data(self):
        """
        Test get data using df_signal date
        """
        self.backtest.get_data()

        self.assertEqual(type(self.backtest.df_stock), pd.DataFrame)
        self.assertTrue(len(self.backtest.df_stock))

        print self.backtest.df_stock.head(20).to_string(line_width=1000)

    def test_get_extra(self):
        """
        Test get extra data using create_order date
        """
        self.backtest.create_order = lambda df_stock, df_signal, df_contract, df_option: False

        self.backtest.get_extra()
        self.assertEqual(type(self.backtest.df_contract), pd.DataFrame)
        self.assertGreater(len(self.backtest.df_option), 0)

    def test_set_commission(self):
        """
        Test set commission for backtest trade
        """
        print 'run set_commission...'
        self.backtest.set_commission(self.commission)

        print 'commission: %s' % self.backtest.commission
        self.assertEqual(type(self.backtest.commission), Commission)

    def test_calc_stock_qty(self):
        """
        Test calculate stock quantity
        """
        prices = [53.23, 12.71, 735.69, 94.50, 6.22]
        quantities = [1, -3, -7, 4, 9]
        capitals = [10000, 20000, 15000, 7600, 900]

        print 'run calc_stock_qty...'
        for price, stock_qty, capital in zip(prices, quantities, capitals):
            print 'price: %.2f, qty: %.2f, capital: %.2f' % (
                price, stock_qty, capital
            ),
            qty = self.backtest.calc_stock_qty(price, stock_qty, capital)
            amount = qty * price
            if stock_qty > 0:
                extra = capital - amount
            else:
                extra = capital + amount
            print 'result: %d, amount: %.2f, extra: %.2f' % (
                qty, amount, extra
            )
            self.assertGreater(extra, 0)
            self.assertFalse(qty % stock_qty)

    def test_calc_option_qty(self):
        """
        Test calculate option quantity
        """
        prices = [3.23, 12.71, 1.35, 4.50, 0.69]
        quantities = [1, 2, -7, -3, 9]
        capitals = [1000, 4000, 1500, 7600, 3200]

        print 'run calc_option_qty...'
        for price, option_qty, capital in zip(prices, quantities, capitals):
            print 'price: %.2f, qty: %.2f, capital: %.2f' % (
                price, option_qty, capital
            ),
            qty = self.backtest.calc_option_qty(price, option_qty, capital)
            amount = qty * price * 100
            if option_qty > 0:
                extra = capital - amount
            else:
                extra = capital + amount
            print 'result: %d, amount: %.2f, extra: %.2f' % (
                qty, qty * price * 100, extra
            )

            self.assertFalse(qty % option_qty)
            self.assertGreater(extra, 0)

    def test_calc_covered_qty(self):
        """
        Test calculate covered quantity
        """
        prices = [3.23, 12.71, 1.35, 4.50]
        quantities = [(100, 1), (-100, -1), (100, -1), (-100, 1)]
        capitals = [1000, 40000, 15000, 960]

        print 'run calc_covered_qty...'
        for price, covered_qty, capital in zip(prices, quantities, capitals):
            print 'price: %.2f, qty: %s, capital: %.2f' % (
                price, covered_qty, capital
            ),
            qty = self.backtest.calc_covered_qty(price, covered_qty[0], covered_qty[1], capital)
            amount = qty[0] * price
            if covered_qty[0] > 0:
                extra = capital - amount
            else:
                extra = capital + amount

            print 'result: %s, amount: %.2f, extra: %.2f' % (
                qty, amount, extra
            )

            self.assertFalse(qty[0] % covered_qty[0])
            self.assertFalse(qty[1] % covered_qty[1])

    def test_calc_quantity(self):
        """
        Test calculate trade quantity
        """
        prices = [3.23, 12.71, 1.35, 4.50, 0.69]
        quantities = [(0, 1), (2, 0), (100, -1), (100, 1), (0, 3)]
        capitals = [1000, 4000, 1500, 7600, 3200]

        print 'run calc_covered_qty...'
        for price, (sqm, oqm), capital in zip(prices, quantities, capitals):
            print 'price: %.2f, sqm: %.2f, oqm: %.2f, capital: %.2f' % (
                price, sqm, oqm, capital
            ),
            sqty, oqty = self.backtest.calc_quantity(price, sqm, oqm, capital)

            print 'stock qty: %.2f, option qty: %.2f' % (sqty, oqty)

    def test_calc_amount(self):
        """
        Test calculate amount capital use for trade
        """
        prices = [3.23, 12.71, 1.35, 4.50, 0.69]
        quantities = [(0, 3), (312, 0), (-1000, 10), (1600, 16), (0, 45)]
        capitals = [1000, 4000, 1500, 7600, 3200]

        print 'run calc_amount...'
        for price, (sqty, oqty), capital in zip(prices, quantities, capitals):
            print 'price: %.2f, sqty: %.2f, oqty: %.2f, capital: %.2f' % (
                price, sqty, oqty, capital
            ),
            amount, extra = self.backtest.calc_amount(price, sqty, oqty, capital)

            print 'amount: %.2f, extra: %.2f' % (amount, extra)
            self.assertTrue(amount)
            self.assertTrue(extra)
            self.assertLess(amount, capital)
            self.assertLess(extra, capital)
            self.assertEqual(amount + extra, capital)

    def test_calc_fee(self):
        """
        Test calculate amount capital use for trade
        """
        quantities = [(0, 3), (312, 0), (-1000, 10), (1600, 16), (0, 45)]

        print 'run calc_fee...'
        for sqty, oqty in quantities:
            print 'sqty: %.2f, oqty: %.2f' % (sqty, oqty),
            fee = self.backtest.calc_fee(sqty, oqty)

            print 'fee: %.2f' % fee
            self.assertTrue(fee)

    def test_make_trade(self):
        """
        Test make df_trade using create_order
        """
        args = {'side': 'follow'}
        self.backtest.get_data()
        self.backtest.get_extra()
        df_trade = self.backtest.make_trade(**args)

        print df_trade.to_string(line_width=1000)
        print df_trade.dtypes
        columns = [
            'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1', 'holding',
            'sqty0', 'sqty1', 'oqty0', 'oqty1', 'amount0', 'fee0', 'remain0',
            'amount1', 'fee1', 'net_chg', 'remain1', 'pct_chg'
        ]
        for column in df_trade.columns:
            self.assertIn(column, columns)

        self.assertEqual(type(df_trade), pd.DataFrame)
        self.assertGreater(len(df_trade), 0)

    def test_report(self):
        """
        Test make report using df_trade
        """
        args = {'side': 'follow', 'percent': 5}
        self.backtest.get_data()
        self.backtest.get_extra()
        df_trade = self.backtest.make_trade(**args)

        report = self.backtest.report(df_trade)

        print pd.DataFrame([report]).to_string(line_width=1000)

    def test_generate(self):
        """
        Test generate a df_report and df_trades
        """
        self.backtest.get_data()
        self.backtest.get_extra()
        self.backtest.set_args(fields={
            'side': 'follow,reverse,buy,sell',
            'percent': '0:10:5'
        })
        df_report, df_trades = self.backtest.generate()

        print df_report.to_string(line_width=1000)
        print df_trades.head(10).to_string(line_width=1000)

        self.assertEqual(type(df_report), pd.DataFrame)
        self.assertEqual(type(df_trades), pd.DataFrame)
        self.assertTrue(len(df_report))
        self.assertTrue(len(df_trades))

    def test_save(self):
        """
        Test save df_reports and df_signals
        """
        self.backtest.save(
            fields={
                'side': 'follow,reverse,buy,sell',
                'percent': '0:10:5'
            },
            formula=self.formula,
            report_id=self.report.name,
            df_signal=self.df_signal,
            commission=self.commission,
            capital=self.capital
        )

        db = pd.HDFStore(os.path.join(RESEARCH, self.symbol.lower(), 'strategy.h5'))

        df_report = db.select('report')
        df_trades = db.select('trade')
        db.close()

        print df_report.head().to_string(line_width=1000)
        print df_trades.head().to_string(line_width=1000)

        self.assertEqual(type(df_report), pd.DataFrame)
        self.assertEqual(type(df_trades), pd.DataFrame)
        self.assertTrue(len(df_report))
        self.assertTrue(len(df_report))


class TestStrategyAnalysisView(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.formula = Formula.objects.get(rule='Ewma Chg D')
        self.report_id = 1
        self.trade = Trade.objects.get(id=1)
        self.commission = Commission.objects.get(id=1)
        self.capital = 5000

    def test_form_analysis(self):
        """
        Test form analysis after set arguments
        """
        form = StrategyAnalysisForm2(
            arguments=self.trade.get_args(),
            data={
                'side': 'follow'
            }
        )

        print 'form valid: %s' % self.trade.get_args()
        self.assertTrue(form.is_valid())

        form.analysis(**{
            'symbol': self.symbol.lower(),
            'formula_id': self.formula.id,
            'report_id': self.report_id,
            'trade_id': self.trade.id,
            'commission_id': self.commission.id,
            'capital': self.capital,
        })

        print '-' * 70

    # todo: cont















