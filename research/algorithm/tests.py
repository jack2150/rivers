from base.utests import *
import pandas as pd
from data.models import Underlying
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from research.algorithm.backtest import FormulaBacktest
from research.algorithm.models import Formula
from research.algorithm.views import AlgorithmAnalysisForm
from rivers.settings import RESEARCH


class TestAlgorithm(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.algorithm = Formula.objects.get(rule='Ewma Chg D')

    def test_start_backtest(self):
        """
        Test make quant instance using algorithm methods
        """
        quant = self.algorithm.start_backtest()
        print quant

        self.assertEqual(type(quant), FormulaBacktest)

        self.assertTrue(quant.handle_data)
        self.assertTrue(quant.handle_data)

    def test_get_args(self):
        """
        Test get arguments from handle_data and create_signal
        """
        args = self.algorithm.get_args()

        print args

        self.assertListEqual(
            args,
            [('handle_data_span', 0),
             ('handle_data_previous', 0)]
        )


class TestAlgorithmAnalysis(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.algorithm = Formula.objects.get(rule='Ewma Chg D')

        try:
            self.underlying = Underlying()
            self.underlying.symbol = 'AIG'
            self.underlying.start_date = '2009-01-01'
            self.underlying.stop_date = '2016-01-01'
        except IntegrityError:
            self.underlying = Underlying.objects.get(symbol='AIG')

    def test_view(self):
        """
        Test ready algorithm form before start testing
        """
        response = self.client.get(reverse('admin:algorithm_analysis', args=(1, 0)))

        form = response.context['form']

        for key in form.initial.keys():
            print key, form.initial[key]

        self.assertTrue(form.initial['formula_id'])
        self.assertEqual(form.initial['formula_rule'],
                         'Ewma Chg D')
        self.assertTrue(form.initial['formula_equation'],
                        'EMA = EMA(t)(k-1) - EMA(t-1)(k-1)')

        # arguments exists
        print 'arguments that use for testing...'
        for key in ('handle_data_span', 'handle_data_previous'):
            print key, form[key]
            self.assertTrue(form[key])


class TestAlgorithmAnalysisForm(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.formula = Formula.objects.get(rule='Ewma Chg D - H')
        self.arguments = self.formula.get_args()

        self.data = {
            'symbol': self.symbol,
            'start_date': '2013-01-01',
            'stop_date': '2014-12-31',
            'handle_data_span': '60',
            'handle_data_previous': '20',
            'create_signal_holding': '20',
            'formula_id': self.formula.id,
            'formula_rule': self.formula.rule,
            'formula_equation': self.formula.equation
        }

    def test_algorithm_analysis_form_is_valid(self):
        """
        Test run algorithm test form is valid
        """
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=self.data)
        print 'form is valid using valid input data...\n'
        print self.form.errors
        self.assertTrue(self.form.is_valid())

        print 'testing with invalid input data...'

        self.data['formula_id'] = '-1'
        self.data['symbol'] = 'XXL'
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=self.data)
        print self.form.errors.items()
        self.assertFalse(self.form.is_valid())
        self.assertIn('Formula id', self.form.errors['formula_id'].__str__())
        self.assertIn('is not found', self.form.errors['formula_id'].__str__())
        self.assertIn('Symbol', self.form.errors['symbol'].__str__())
        self.assertIn('not found', self.form.errors['symbol'].__str__())
        self.data['algorithm_id'] = self.formula.id
        self.data['handle_data_span'] = 'abc'
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=self.data)
        print self.form.errors.items()
        # self.assertIn('Handle_data_span', self.form.errors['handle_data_span'].__str__())
        # self.assertIn('ValueError', self.form.errors['handle_data_span'].__str__())

    def test_algorithm_analysis_form_analysis(self):
        """
        Test algorithm analysis form analysis method
        """
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=self.data)
        self.assertTrue(self.form.is_valid())

        # run analysis
        self.form.analysis()

        db = pd.HDFStore(os.path.join(RESEARCH, self.symbol.lower(), 'algorithm.h5'))
        df_report = db.select('report')
        df_signal = db.select('signal')
        db.close()

        print df_report.head().to_string(line_width=1000)
        print df_signal.head().to_string(line_width=1000)

        self.assertEqual(type(df_report), pd.DataFrame)
        self.assertEqual(type(df_signal), pd.DataFrame)
        self.assertTrue(len(df_report))
        self.assertTrue(len(df_report))


class TestFormulaBacktest(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'  # can be a single symbol or list of symbols
        self.formula = Formula.objects.get(rule='Ewma Chg D')
        self.formula.start_backtest()
        self.backtest = self.formula.backtest

        self.arguments = ('span', 'previous', 'holding')
        self.hd_args = {
            'span': 20,
            'previous': 20
        }
        self.cs_args = {}

    def test_set_args(self):
        """
        Test generate a list of valid argument values
        """
        self.backtest.set_args(fields={
            'handle_data_span': '120:240:20',
            'handle_data_previous': '20:40:20',
            'create_signal_holding': '30:60:30',
        })

        args = self.backtest.args

        for arg in args:
            print arg
            self.assertEqual(type(arg), dict)
            self.assertListEqual(arg.keys(), ['create_signal', 'handle_data'])

            handle_data = arg['handle_data']
            for key in handle_data.keys():
                self.assertNotIn(key, ('create_signal', 'handle_data'))
                self.assertIn(key, ('span', 'previous'))

            create_signal = arg['create_signal']
            for key in create_signal.keys():
                self.assertNotIn(key, ('create_signal', 'handle_data'))
                self.assertIn(key, ('holding',))

    def test_get_data(self):
        """
        Test get data that require for backtest
        """
        starts = ['2011-01-01', None, '2014-01-01', None]
        stops = ['2012-12-31', '2013-12-31', None, None]

        for start, stop in zip(starts, stops):
            self.backtest.set_symbol_date(self.symbol, start, stop)
            print 'using start: %s stop: %s' % (start, stop)
            print 'run get_data...'
            self.backtest.get_data()

            print 'df_stock length: %d' % len(self.backtest.df_stock)
            print 'df_change length: %d' % len(self.backtest.df_change)
            self.assertTrue(len(self.backtest.df_stock))
            self.assertTrue(len(self.backtest.df_change))

            self.assertEqual(len(self.backtest.df_stock), len(self.backtest.df_change))

            print '.' * 70

    def test_extra_data(self):
        """
        Test get extra data if require for handle_data and create_signal
        """
        self.backtest.set_symbol_date(self.symbol)

        self.backtest.handle_data = lambda df, df_earning, df_dividend, df_contract: False

        self.backtest.extra_data()

        print 'df_earning: %d' % len(self.backtest.df_earning)
        self.assertTrue(len(self.backtest.df_earning))
        print 'df_dividend: %d' % len(self.backtest.df_dividend)
        self.assertTrue(len(self.backtest.df_dividend))
        print 'df_contract: %d' % len(self.backtest.df_contract)
        self.assertTrue(len(self.backtest.df_contract))
        print 'df_option: %d' % len(self.backtest.df_option)
        self.assertTrue(len(self.backtest.df_option))
        self.assertEqual(len(self.backtest.df_option), len(self.backtest.df_all))

    def test_prepare_join(self):
        """
        Prepare data that ready for generate report
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        print 'run prepare_join...'
        self.backtest.prepare_join()

        print 'df_signal length: %d' % len(df_signal)
        print 'df_list length: %d' % len(self.backtest.df_list)
        print 'df_join length: %d' % len(self.backtest.df_join)
        self.assertTrue(len(self.backtest.df_list))
        self.assertEqual(type(self.backtest.df_list), list)
        self.assertTrue(len(self.backtest.df_join))
        self.assertEqual(type(self.backtest.df_join), pd.DataFrame)

    def test_sharpe_ratio(self):
        """
        Test generate sharpe ratio using df_join
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()
        sr1, sr2 = self.backtest.sharpe_ratio()

        print 'sharpe ratio for risk free rate: %.2f%%' % (sr1 * 100)
        print 'sharpe ratio for s&p 500 rate: %.2f%%' % (sr2 * 100)
        self.assertTrue(sr1)
        self.assertTrue(sr2)

    def test_sortino_ratio(self):
        """
        Test generate sharpe ratio using df_join
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()
        sr1, sr2 = self.backtest.sortino_ratio()

        print 'sortino ratio for risk free rate: %.2f%%' % (sr1 * 100)
        print 'sortino ratio for s&p 500 rate: %.2f%%' % (sr2 * 100)
        self.assertTrue(sr1)
        self.assertTrue(sr2)

    def test_buy_hold(self):
        """
        Test calculate buy and hold
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()
        print 'run buy_hold...'
        bh = self.backtest.buy_hold()
        print 'buy and hold: %.2f%%' % (bh * 100)
        self.assertTrue(bh)

    def test_profit_loss(self):
        """
        Test calculate profit loss detail
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()

        print 'run profit_loss...'
        pl_sum, pl_cumprod, pl_mean, pl_std = self.backtest.profit_loss()
        print 'pl_sum: %.2f%%' % (pl_sum * 100)
        print 'pl_cumprod: %.2f%%' % (pl_cumprod * 100)
        print 'pl_mean: %.2f%%' % (pl_mean * 100)
        print 'pl_std: %.2f%%' % (pl_std * 100)
        self.assertTrue(pl_sum)
        self.assertTrue(pl_cumprod)
        self.assertTrue(pl_mean)

    def test_trade_summary(self):
        """
        Test trade summary for profit loss and chance
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()
        summary = self.backtest.trade_summary()

        print 'pl_count: %d' % summary[0]
        print 'profit_count: %d' % summary[1]
        print 'profit_chance: %.2f%%' % (summary[2] * 100)
        print 'loss_count: %d' % summary[3]
        print 'loss_chance: %.2f%%' % (summary[4] * 100)
        print 'profit_max: %.2f%%' % (summary[5] * 100)
        print 'profit_min: %.2f%%' % (summary[6] * 100)
        print 'loss_max: %.2f%%' % (summary[7] * 100)
        print 'loss_min: %.2f%%' % (summary[8] * 100)

    def test_value_at_risk(self):
        """
        Test trade summary for profit loss and chance
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()
        var_99, var_95 = self.backtest.value_at_risk()
        print 'var_99: %.2f%%' % (var_99 * 100)
        print 'var_95: %.2f%%' % (var_95 * 100)
        self.assertTrue(var_99)
        self.assertTrue(var_95)

    def test_draw_down(self):
        """
        Test calculate the draw down effect
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()
        mdd = self.backtest.max_draw_down()
        print 'max draw down: %.2f%%' % (mdd * 100)
        self.assertTrue(mdd)

    def test_holding_period(self):
        """
        Test calculate the draw down effect
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        self.backtest.set_signal(df_signal)
        self.backtest.prepare_join()
        holding_period = self.backtest.holding_period()
        # day_profit_count, day_profit_mean, day_loss_count, day_loss_mean
        print 'day_profit_count: %.2d' % holding_period[0]
        print 'day_profit_chance: %.2f%%' % (holding_period[1] * 100)
        print 'day_profit_mean: %.2f%%' % (holding_period[2] * 100)
        print 'day_loss_count: %.2d' % holding_period[3]
        print 'day_loss_chance: %.2f%%' % (holding_period[4] * 100)
        print 'day_loss_mean: %.2f%%' % (holding_period[5] * 100)
        self.assertTrue(holding_period[0])
        self.assertTrue(holding_period[1])
        self.assertTrue(holding_period[2])
        self.assertTrue(holding_period[3])
        self.assertTrue(holding_period[4])
        self.assertTrue(holding_period[5])

    def test_report(self):
        """
        Test make report using df_signal
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)
        report = self.backtest.report(df_signal)

        for key, value in report.items():
            print '%s: %s' % (key, value)
        self.assertEqual(type(report), dict)

    def test_generate(self):
        """
        Test start backtest for all formula args
        """
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()
        self.backtest.set_args(fields={
            'handle_data_span': '120:240:20',
            'handle_data_previous': '20:40:20',
            'create_signal_holding': '30:60:30',
        })
        df_reports, df_signals = self.backtest.generate()

        self.assertEqual(type(df_reports), pd.DataFrame)
        self.assertEqual(type(df_signals), pd.DataFrame)
        self.assertTrue(len(df_reports))
        self.assertTrue(len(df_signals))

    def test_save(self):
        """
        Test save df_reports and df_signals
        """
        self.backtest.save(
            fields={
                'handle_data_span': '120:240:20',
                'handle_data_previous': '20:40:20',
                'create_signal_holding': '30:60:30',
            },
            symbol=self.symbol,
            start='2009-01-01',
            stop='2014-12-31'
        )

        db = pd.HDFStore(os.path.join(RESEARCH, self.symbol.lower(), 'algorithm.h5'))

        df_report = db.select('report')
        df_signal = db.select('signal')
        db.close()

        print df_report.head().to_string(line_width=1000)
        print df_signal.head().to_string(line_width=1000)

        self.assertEqual(type(df_report), pd.DataFrame)
        self.assertEqual(type(df_signal), pd.DataFrame)
        self.assertTrue(len(df_report))
        self.assertTrue(len(df_report))


class TestBacktestTradeView(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'
        self.formula = Formula.objects.first()

    def test_algorithm_report_view(self):
        """
        Test empty algorithm report view page
        """
        self.client.get(reverse(
            'admin:algorithm_report_view', kwargs={
                'symbol': self.symbol.lower(),
                'formula_id': self.formula.id
            }
        ))

    def test_algorithm_report_json(self):
        """
        Test algorithm report json data
        """
        response = self.client.get(reverse(
            'admin:algorithm_report_json', kwargs={
                'symbol': self.symbol.lower(),
                'formula_id': self.formula.id,

            },
        ), {
            'draw': 1,
            'order[0][column]': 0,
            'order[0][dir]': 0,
            'start': 0,
            'length': 10
        })

        print response

    def test_algorithm_signal_view(self):
        """
        Test algorithm df_signal view for a report
        """
        self.client.get(reverse(
            'admin:algorithm_signal_view', kwargs={
                'symbol': self.symbol.lower(),
                'formula_id': self.formula.id,
                'backtest_id': 1
            }
        ))

    def test_algorithm_trade_view(self):
        """
        Test deep df_list view for a report
        """
        self.client.get(reverse(
            'admin:algorithm_trade_view', kwargs={
                'symbol': self.symbol.lower(),
                'formula_id': self.formula.id,
                'backtest_id': 1
            }
        ))
