from base.utests import TestUnitSetUp
from statement.position.views import *


class TestPositionSpreads(TestUnitSetUp):
    def test_view(self):
        self.client.get(reverse('admin:position_spreads', kwargs={'date': '2015-01-30'}))


class TestBlindStrategySpreads(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.position = Position.objects.filter(symbol='WFC').first()
        self.strategy_result = StrategyResult.objects.filter(symbol='WFC').first()

    def test_blind_strategy_form_is_valid(self):
        """
        Test blind position form is valid
        """
        form = BlindPositionForm(data={
            'position': self.position.id,
            'strategy_result': self.strategy_result.id
        })
        self.assertTrue(form.is_valid())

        # invalid
        form = BlindPositionForm(data={
            'position': 1,
            'strategy_result': 100
        })
        self.assertFalse(form.is_valid())

        # different symbol
        strategy_result = StrategyResult.objects.exclude(symbol='WFC').first()
        form = BlindPositionForm(data={
            'position': self.position.id,
            'strategy_result': strategy_result.id
        })
        self.assertFalse(form.is_valid())


class TestPositionReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.position = Position.objects.filter(symbol='WFC').last()
        #self.date = '2015-02-06'
        self.date = '2015-03-30'

        print self.position, self.date

    def test_view(self):
        self.client.get(
            reverse('admin:position_report', kwargs={'id': self.position.id, 'date': self.date})
        )



