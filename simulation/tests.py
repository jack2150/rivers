from base.tests import TestSetUp
from simulation.views import *


class TestStrategyAnalysisForm1(TestSetUp):
    fixtures = ('quant_data.json', 'sim_data.json')

    def setUp(self):
        TestSetUp.setUp(self)

        self.algorithm_result = AlgorithmResult.objects.first()

        self.data = {
            'algorithmresult_id': self.algorithm_result.id,
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
            ),
            'strategy': 1
        }

    def test_is_valid(self):
        """
        Test simulation analysis form
        """
        print 'form is valid using valid input data...\n'
        self.form = StrategyAnalysisForm1(data=self.data)
        self.assertTrue(self.form.is_valid())

        print 'testing with invalid input data...'
        self.data['algorithmresult_id'] = -1
        self.data['strategy'] = -1
        self.form = StrategyAnalysisForm1(data=self.data)

        self.assertFalse(self.form.is_valid())
        self.assertIn('Algorithm result id does not exists.',
                      self.form.errors['algorithmresult_id'].__str__())
        self.assertIn('Strategy does not exists.',
                      self.form.errors['strategy'].__str__())

        for error in self.form.errors.items():
            print error


class TestStrategyAnalysisForm2(TestSetUp):
    fixtures = ('quant_data.json', 'sim_data.json')

    def setUp(self):
        TestSetUp.setUp(self)

        self.algorithm_result = AlgorithmResult.objects.first()
        """:type: AlgorithmResult"""
        self.strategy = Strategy.objects.get(name='Stop Loss')
        self.commission = Commission.objects.first()
        self.capital = 13721.25

        underlying = Underlying()
        underlying.symbol = self.algorithm_result.symbol.upper()
        underlying.start = '2009-01-01'
        underlying.stop = '2016-01-01'
        underlying.save()

        underlying2 = Underlying()
        underlying2.symbol = 'SPY'
        underlying2.start = '2009-01-01'
        underlying2.stop = '2016-01-01'
        underlying2.save()

        print self.algorithm_result.symbol

        self.data = {
            'symbol': self.algorithm_result.symbol,
            'algorithm_name': self.algorithm_result.algorithm.rule,
            'algorithm_args': self.algorithm_result.arguments,
            'algorithmresult_id': self.algorithm_result.id,
            'strategy_id': self.strategy.id,
            'strategy': self.strategy.name,
            'capital': self.capital,
            'order': 'gtc',
            'percent': 7,
            'commission': self.commission.id
        }

        self.arguments = self.strategy.get_args()

    def tearDown(self):
        TestSetUp.tearDown(self)

        strategy_results = StrategyResult.objects.filter(capital0=self.capital).all()
        strategy_results.delete()

    def test_is_valid(self):
        """
        Test strategy analysis form is valid
        """
        print 'form is valid using valid input data...\n'
        self.form = StrategyAnalysisForm2(arguments=self.arguments, data=self.data)
        self.assertTrue(self.form.is_valid())

        # testing errors
        print 'testing with invalid input data...'
        self.data['algorithmresult_id'] = -1
        self.data['strategy_id'] = -1
        self.form = StrategyAnalysisForm2(arguments=self.arguments, data=self.data)
        self.assertFalse(self.form.is_valid())
        self.assertIn('Algorithm result id does not exists.',
                      self.form.errors['algorithmresult_id'].__str__())
        self.assertIn('Strategy id does not exists.',
                      self.form.errors['strategy_id'].__str__())

        print 'testing valid strategy with invalid arguments...'
        self.data['algorithmresult_id'] = self.algorithm_result.id
        self.data['strategy_id'] = self.strategy.id
        self.data['order'] = 'abc'
        self.data['percent'] = -1
        self.form = StrategyAnalysisForm2(arguments=self.arguments, data=self.data)
        self.assertFalse(self.form.is_valid())
        self.assertIn('Percent value can only be positive.',
                      self.form.errors['percent'].__str__())
        self.assertIn('KeyError Order field value.',
                      self.form.errors['order'].__str__())

        for key, error in self.form.errors.items():
            print key, error

    def test_analysis(self):
        """
        Test analysis strategy that save report result into db
        """
        self.form = StrategyAnalysisForm2(arguments=self.arguments, data=self.data)
        self.assertTrue(self.form.is_valid())

        self.form.analysis()

        strategy_results = StrategyResult.objects.filter(capital0=self.capital).all()
        self.assertTrue(strategy_results.count())

        for strategy_result in strategy_results:
            print strategy_result
            self.assertEqual(strategy_result.algorithm_result.id, self.algorithm_result.id)
            self.assertEqual(strategy_result.strategy.id, self.strategy.id)
