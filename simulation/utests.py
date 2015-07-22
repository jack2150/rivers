from base.utests import TestUnitSetUp
from simulation.views import *
import pandas as pd


# noinspection PyArgumentList
class TestStrategy(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.algorithm = Algorithm.objects.get(rule='EWMA change direction')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.quant.arguments = {'span': 120, 'previous': 20}
        self.df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.quant.arguments)
        self.df_signal = self.quant.create_signal(self.df_stock)

        self.strategy = Strategy.objects.get(id=1)

    def test_get_arguments(self):
        """
        Test get arguments from strategy trade method
        """
        args = self.strategy.get_args()

        print args

        self.assertEqual(type(args), list)
        self.assertEqual(args[0], ('order', ('gtc', 'close')))
        self.assertEqual(args[1], ('percent', 0))

    def test_make_order(self):
        """
        Test make strategy order
        """
        self.strategy.arguments = {
            'order': 'gtc',
            'percent': 5
        }

        df_order = self.strategy.make_order(
            self.df_stock, self.df_signal, **self.strategy.arguments
        )

        print df_order.to_string(line_width=200)

        expected_columns = [
            'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1',
            'holding', 'pct_chg', 'time1', 'sqm0', 'sqm1', 'oqm0', 'oqm1'
        ]
        for column in df_order.columns:
            self.assertIn(column, expected_columns)

        expected_dtypes = [
            'object', 'object', 'object', 'object', np.float64, np.float64,
            np.int32, np.float64, 'object', np.int64, np.int64, np.int64, np.int64
        ]

        print '\n' + 'checking data types...'
        dtypes = {key: value for key, value in zip(expected_columns, expected_dtypes)}
        for key, dtype in df_order.dtypes.iteritems():
            print key, dtype
            self.assertTrue(dtype == dtypes[key])


class TestStrategyQuant(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.algorithm_result = AlgorithmResult.objects.first()
        self.strategy = Strategy.objects.get(name='Stop Loss')
        self.commission = Commission.objects.first()
        self.capital = 10000.00

        self.strategy_quant = StrategyQuant(
            algorithmresult_id=self.algorithm_result.id,
            strategy_id=self.strategy.id,
            commission_id=self.commission.id,
            capital=self.capital
        )

        self.args = {
            'order': 'gtc',
            'percent': 5
        }

    def test_set_args(self):
        """
        Test set arguments that ready for strategy test
        """
        self.strategy_quant.set_args({
            'order': ('gtc', 'close'),
            'percent': '0:20:1'
        })

        self.assertEqual(len(self.strategy_quant.args), 42)

        for arg in self.strategy_quant.args:
            print arg
            self.assertEqual(type(arg), dict)
            self.assertEqual(len(arg), 2)
            self.assertIn(arg['order'], ('gtc', 'close'))
            self.assertIn(arg['percent'], np.arange(21))

    def test_calc_fees(self):
        """
        Test calculate fees for each trade in df_order
        """
        quantities = [(1, 0), (100, 1), (0, 1), (0, 15)]
        expected = [15.99, 17.49, 1.5, 22.5]

        for quantity, expect in zip(quantities, expected):
            fees = self.strategy_quant.calc_fee(quantity[0], quantity[1])
            print 'value: %s, fees: %s' % (quantity, fees)

            self.assertEqual(float(fees), expect)

    def test_calc_qty(self):
        """
        Test calculate quantity for each trade in df_order
        """
        closes = [6.78, 6.55, 1.96]
        quantities = [(1, 0), (0, 1), (100, 1)]
        expected = [(1472, 0), (0, 15), (5000, 50)]

        for close, quantity, expect in zip(closes, quantities, expected):
            qty = self.strategy_quant.calc_qty(close, quantity[0], quantity[1])
            print 'close0: %s, value: %s, quantity: %s' % (close, quantity, qty)
            self.assertEqual(qty, expect)

    def test_calc_capital(self):
        """

        :return:
        """
        closes = [15.78, 6.55, 1.96]
        quantities = [(633, 0), (1500, 15), (0, 51)]
        expected = [9988.74, 9825.0, 9996]
        for close, quantity, expect in zip(closes, quantities, expected):
            capital = self.strategy_quant.calc_capital(
                close, quantity[0], quantity[1]
            )
            print 'capital: %s, close0: %s, value: %s, quantity: %s' % (
                capital, close, quantity, quantity
            )
            self.assertEqual(capital, expect)

    def test_make_trade(self):
        """
        Test make trade using strategy, arguments, capital and commission
        """
        df_trade = self.strategy_quant.make_trade(**self.args)
        self.assertEqual(type(df_trade), pd.DataFrame)
        self.assertGreater(df_trade['date0'].count(), 1)

        print df_trade.to_string(line_width=300)

        expected_columns = (
            'amount0', 'amount1', 'capital', 'close0', 'close1', 'date0', 'date1', 'fee0', 'fee1',
            'holding', 'oqty0', 'oqty1', 'pct_chg', 'remain', 'roi', 'signal0', 'signal1',
            'sqty0', 'sqty1', 'time1', 'roi', 'roi_pct_chg'
        )

        for column in df_trade.columns:
            self.assertIn(column, expected_columns)

    def test_make_trade_cumprod(self):
        """
        Test make trade cumprod using strategy, arguments, capital and commission
        """
        df_trade = self.strategy_quant.make_trade_cumprod(**self.args)
        self.assertEqual(type(df_trade), pd.DataFrame)
        self.assertGreater(df_trade['date0'].count(), 1)

        print df_trade.to_string(line_width=300)

        expected_columns = (
            'amount0', 'amount1', 'capital', 'close0', 'close1', 'date0', 'date1', 'fee0', 'fee1',
            'holding', 'oqty0', 'oqty1', 'pct_chg', 'remain', 'roi', 'signal0', 'signal1',
            'sqty0', 'sqty1', 'time1'
        )

        for column in df_trade.columns:
            self.assertIn(column, expected_columns)

    def test_report(self):
        """
        Test making report using strategy trade
        """
        df_trade = self.strategy_quant.make_trade(**self.args)
        df_cumprod = self.strategy_quant.make_trade_cumprod(**self.args)

        report = self.strategy_quant.report(df_trade, df_cumprod)
        self.assertEqual(type(report), dict)

        print list(report.keys())

        expected_keys = (
            'capital0', 'capital1', 'remain_mean',
            'fee_mean', 'fee_sum', 'roi_mean', 'roi_sum'
        )

        for key in expected_keys:
            self.assertIn(key, report.keys())

        print pd.Series(report)

        # try save
        print '\n' + 'test save...'
        strategy_result = StrategyResult(**report)
        strategy_result.symbol = self.algorithm_result.symbol
        strategy_result.algorithm_result = self.algorithm_result
        strategy_result.strategy = self.strategy
        strategy_result.arguments = self.args.__str__()
        strategy_result.commission = self.commission
        strategy_result.save()
        self.assertTrue(strategy_result.id)
        strategy_result.delete()

    def test_make_reports(self):
        """
        Test make a list of report using same strategy, capital,
        commission but using different arguments
        """
        self.strategy_quant.set_args({
            'order': 'gtc',
            'percent': '10:15:5'
        })

        reports = self.strategy_quant.make_reports()
        self.assertEqual(type(reports), list)

        data = list()
        for report in reports:
            self.assertEqual(type(report), dict)
            data.append(report)
        else:
            df_report = pd.DataFrame(data)
            print df_report.to_string(line_width=300)


class TestStrategyAnalysis(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.algorithm_result = AlgorithmResult.objects.first()
        self.strategy = Strategy.objects.get(name='Stop Loss')
        self.commission = Commission.objects.first()
        self.capital = 13721.25

        self.args = {
            'order': 'gtc',
            'percent': 7
        }

    def test_view1(self):
        """
        Test strategy analysis form 1 that all form field is valid
        """
        response = self.client.get(reverse('admin:strategy_analysis1', kwargs={
            'algorithmresult_id': self.algorithm_result.id
        }))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(int(response.context['form']['algorithmresult_id'].value()),
                         self.algorithm_result.id)
        self.assertEqual(response.context['form']['symbol'].value(),
                         self.algorithm_result.symbol)
        self.assertFalse(response.context['form']['strategy'].value())

        for field in response.context['form'].fields:
            print field, response.context['form'][field].value()

        # test form submit
        response = self.client.post(reverse('admin:strategy_analysis1', kwargs={
            'algorithmresult_id': self.algorithm_result.id
        }), data={
            'algorithmresult_id': self.algorithm_result.id,
            'strategy': self.strategy.id,
            'symbol': self.algorithm_result.symbol,
            'algorithm_id': self.algorithm_result.algorithm.id,
            'algorithm_rule': self.algorithm_result.algorithm.rule,
            'algorithm_args': self.algorithm_result.arguments,
            'sharpe_ratio': self.algorithm_result.sharpe_spy,
            'probability': 'Profit: {profit} ; Loss: {loss}'.format(
                profit=self.algorithm_result.profit_prob,
                loss=self.algorithm_result.loss_prob
            ),
            'profit_loss': 'Sum: {pl_sum}, CP: {pl_cumprod}, Mean: {pl_mean}'.format(
                pl_sum=self.algorithm_result.pl_sum,
                pl_cumprod=self.algorithm_result.pl_cumprod,
                pl_mean=self.algorithm_result.pl_mean,
            ),
            'risk': 'Max DD: {max_dd}, VaR 99%: {var99}'.format(
                max_dd=self.algorithm_result.max_dd,
                var99=self.algorithm_result.var_pct99
            )
        })

        # check redirect work
        self.assertIn(
            reverse('admin:strategy_analysis2', kwargs={
                'algorithmresult_id': self.algorithm_result.id,
                'strategy_id': self.strategy.id
            }),
            response.url
        )
        self.assertEqual(response.status_code, 302)

    def test_view2(self):
        """
        Test strategy analysis form 1 that all form field is valid
        """
        response = self.client.get(reverse('admin:strategy_analysis2', kwargs={
            'algorithmresult_id': self.algorithm_result.id,
            'strategy_id': self.strategy.id
        }))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(int(response.context['form']['algorithmresult_id'].value()),
                         self.algorithm_result.id)
        self.assertEqual(response.context['form']['strategy_id'].value(), self.strategy.id)

        for field in response.context['form'].fields:
            print field, response.context['form'][field].value()

        response = self.client.post(reverse('admin:strategy_analysis2', kwargs={
            'algorithmresult_id': self.algorithm_result.id,
            'strategy_id': self.strategy.id
        }), data={
            'symbol': self.algorithm_result.symbol,
            'algorithmresult_id': self.algorithm_result.id,
            'algorithm_id': self.algorithm_result.algorithm.id,
            'algorithm_name': self.algorithm_result.algorithm.rule,
            'algorithm_args': self.algorithm_result.arguments,
            'strategy_id': self.strategy.id,
            'strategy': self.strategy.name,
            'capital': self.capital,
            'commission': self.commission.id,
            'order': self.args['order'],
            'percent': self.args['percent']
        })

        # check redirect work
        self.assertIn(
            reverse('admin:simulation_strategyresult_changelist'),
            response.url
        )
        self.assertEqual(response.status_code, 302)

        # remove test strategy result
        strategy_results = StrategyResult.objects.filter(capital0=self.capital)
        self.assertGreaterEqual(strategy_results.count(), 1)
        for strategy_result in strategy_results:
            strategy_result.delete()
