from base.utests import *
from quant.analysis import Quant
import pandas as pd
from quant.models import Algorithm
from quant.views import AlgorithmAnalysisForm


class TestQuant(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'  # can be a single symbol or list of symbols
        self.algorithm = Algorithm.objects.get(id=5)
        handle_data, create_signal = self.algorithm.get_module()

        self.quant = Quant()
        self.quant.handle_data = handle_data
        self.quant.create_signal = create_signal

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

        print data[self.symbol].tail().to_string(line_width=200)
        print data['FSLR'].tail().to_string(line_width=200)

        self.assertEqual(type(data), pd.Panel)
        self.assertEqual(type(data[self.symbol]), pd.DataFrame)
        self.assertGreaterEqual(
            data[self.symbol][data[self.symbol]['earning']]['date'].count(),
            26
        )

    # noinspection PyArgumentList
    def test_report(self):
        """
        Test using both df_stock and df_signal generate quant report
        """
        df = self.quant.make_df(self.symbol)
        df_stock = self.quant.handle_data(df, 120, 20)
        df_signal = self.quant.create_signal(df_stock)

        report = self.quant.report(df_stock, df_signal)

        expected_keys = (
            'max_loss', 'sortino_rf', 'sharpe_rf', 'buy_hold', 'mean_result', 'profit_trades', 'loss_prob',
            'var_pct99', 'trades', 'sharpe_spy', 'sum_result', 'sortino_spy', 'cumprod_result',
            'loss_trades', 'max_profit', 'var_pct95', 'profit_prob',
            'max_dd', 'r_max_dd', 'max_bh_dd', 'r_max_bh_dd'
        )

        for key in report.keys():
            print key, report[key]
            self.assertIn(key, expected_keys)


class TestAlgorithmAnalysisForm(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.algorithm = Algorithm.objects.get(id=3)
        self.arguments = (
            'span', 'previous', 'holding'
        )

    def test_algorithm_form_is_valid(self):
        """
        Test run algorithm test form is valid
        """
        data = {
            'symbol': 'AIG',
            'span': '120:240:20',
            'previous': '20',
            'holding': '20',
            'algorithm_id': self.algorithm.id,
            'algorithm_rule': self.algorithm.rule,
            'algorithm_formula': self.algorithm.formula,
        }

        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=data)
        print 'form is valid using valid input data...\n'
        self.assertTrue(self.form.is_valid())

        print 'testing with invalid input data...'
        data['algorithm_id'] = '-1'
        data['symbol'] = 'XXL'
        data['span'] = 'abc'
        self.form = AlgorithmAnalysisForm(arguments=self.arguments, data=data)
        self.assertFalse(self.form.is_valid())
        self.assertIn('Algorithm id', self.form.errors['algorithm_id'].__str__())
        self.assertIn('is not found', self.form.errors['algorithm_id'].__str__())
        self.assertIn('Symbol', self.form.errors['symbol'].__str__())
        self.assertIn('not found', self.form.errors['symbol'].__str__())
        self.assertIn('Span', self.form.errors['span'].__str__())
        self.assertIn('is not valid', self.form.errors['span'].__str__())

        for error in self.form.errors.items():
            print error
