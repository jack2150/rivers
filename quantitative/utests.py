from base.utests import *
from django.db.models import Q
from quantitative.models import Algorithm, AlgorithmResult
from quantitative.views import AlgorithmAnalysisForm
import pandas as pd


# noinspection PyUnresolvedReferences
class TestQuant(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'  # can be a single symbol or list of symbols
        self.algorithm = Algorithm.objects.get(id=3)

        self.quant = self.algorithm.quant

        self.arguments = (
            'span', 'previous', 'holding'
        )

    def test_set_args(self):
        """
        Test generate a list of valid argument values
        """
        self.quant.set_args(fields={
            'handle_data_span': '120:240:20',
            'handle_data_previous': '20:40:20',
            'create_signal_holding': '30:60:30',
        })

        args = self.quant.args

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
                self.assertIn(key, ('holding', ))

    def test_make_df(self):
        """
        Test make data frame using sql data
        """
        df_aig = self.quant.make_df('AIG')

        print df_aig.head()

        self.assertEqual(type(df_aig), pd.DataFrame)
        self.assertGreaterEqual(df_aig['date'].count(), 250)

        for column in df_aig.columns:
            self.assertIn(
                column,
                ('symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'earning')
            )

    def test_get_rf_return(self):
        """
        Test get risk free rate from db
        """
        risk_free = self.quant.get_rf_return()

        print risk_free.head()
        self.assertEqual(type(risk_free), pd.Series)
        self.assertGreaterEqual(risk_free.count(), 250)

    def test_seed_data(self):
        """
        Test seed data into quant model
        """
        self.quant.seed_data([self.symbol, 'FSLR'])
        data = self.quant.data

        print self.quant.data[self.symbol].tail().to_string(line_width=200)
        print self.quant.data['FSLR'].tail().to_string(line_width=200)

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(type(data[self.symbol]), pd.DataFrame)
        self.assertGreaterEqual(
            data[self.symbol][data[self.symbol]['earning']]['date'].count(),
            26
        )

    def test_create_signal2(self):
        """
        Test create signal 2 that add extra columns into df_signal
        """
        df = self.quant.make_df(self.symbol)
        df_stock = self.quant.handle_data(df, 120, 20)
        df_signal = self.quant.create_signal(df_stock, 20)

        df_signal2 = self.quant.create_signal2(df, df_signal)

        print df_signal2.to_string(line_width=400)

        expected_keys = ('mean', 'median', 'max', 'min', 'std')
        for key in expected_keys:
            self.assertIn(key, df_signal2.columns)

        print '\n'
        print df_signal2.dtypes

    # noinspection PyArgumentList
    def test_report(self):
        """
        Test using both df_stock and df_signal generate quant report
        """
        df = self.quant.make_df(self.symbol)
        df_stock = self.quant.handle_data(df, 120, 20)
        df_signal = self.quant.create_signal(df_stock, 20)

        report = self.quant.report(df_stock, df_signal)

        expected_keys = (
            'sharpe_rf', 'sharpe_spy',
            'sortino_rf', 'sortino_spy',
            'bh_sum', 'bh_cumprod',
            'trades', 'profit_trades', 'profit_prob', 'loss_trades', 'loss_prob',
            'max_profit', 'max_loss',
            'pl_sum', 'pl_cumprod', 'pl_mean',
            'var_pct99', 'var_pct95',
            'max_dd', 'r_max_dd', 'max_bh_dd', 'r_max_bh_dd',
            'pct_mean', 'pct_median', 'pct_max', 'pct_min', 'pct_std',
        )

        for key in report.keys():
            print key, report[key]
            self.assertIn(key, expected_keys)

    def test_get_reports(self):
        """
        Test get reports by running all symbols inside data and all arguments
        """
        self.quant.seed_data([self.symbol, 'FSLR'])
        self.quant.set_args(fields={
            'handle_data_span': '20:40:20',
            'handle_data_previous': '20',
            'create_signal_holding': '30',
        })
        reports = self.quant.get_reports()
        self.assertEqual(type(reports), pd.Series)

        for report in reports:
            print report

            for key in ('symbol', 'date', 'algorithm', 'arguments', 'signals'):
                self.assertIn(key, report.keys())


class TestAlgorithmAnalysisForm(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.algorithm = Algorithm.objects.get(id=3)
        self.arguments = (
            'handle_data_span', 'handle_data_previous',
            'create_signal_holding'
        )

        self.data = {
            'symbol': self.symbol,
            'handle_data_span': '261',
            'handle_data_previous': '20',
            'create_signal_holding': '261',
            'algorithm_id': self.algorithm.id,
            'algorithm_rule': self.algorithm.rule,
            'algorithm_formula': self.algorithm.formula,
        }

    def test_algorithm_analysis_form_is_valid(self):
        """
        Test run algorithm test form is valid
        """
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=self.data)
        print 'form is valid using valid input data...\n'
        self.assertTrue(self.form.is_valid())

        print 'testing with invalid input data...'
        self.data['algorithm_id'] = '-1'
        self.data['symbol'] = 'XXL'
        self.data['handle_data_span'] = 'abc'
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=self.data)
        self.assertFalse(self.form.is_valid())
        self.assertIn('Algorithm id', self.form.errors['algorithm_id'].__str__())
        self.assertIn('is not found', self.form.errors['algorithm_id'].__str__())
        self.assertIn('Symbol', self.form.errors['symbol'].__str__())
        self.assertIn('not found', self.form.errors['symbol'].__str__())
        self.assertIn('span', self.form.errors['handle_data_span'].__str__())
        self.assertIn('is not valid', self.form.errors['handle_data_span'].__str__())

        for error in self.form.errors.items():
            print error

    def test_algorithm_analysis_form_analysis(self):
        """
        Test algorithm analysis form analysis method
        """
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=self.data)
        self.assertTrue(self.form.is_valid())

        # run analysis
        algorithm_results = self.form.analysis()

        for algorithm_result in algorithm_results:
            algorithm_result = AlgorithmResult.objects.filter(
                Q(symbol=algorithm_result.symbol) &
                Q(algorithm=algorithm_result.algorithm) &
                Q(arguments=algorithm_result.arguments)
            ).order_by('id').last()

            print algorithm_result
            self.assertTrue(algorithm_result.id)
            algorithm_result.delete()





