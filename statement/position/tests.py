from pprint import pprint
from base.utests import TestUnitSetUp
from statement.position.views import *


class TestPositionSpreads(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.date = Statement.objects.first().date

    def test_view(self):
        response = self.client.get(reverse('admin:position_spreads', kwargs={'date': self.date}))

        print response


class TestBlindStrategySpreads(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        position_symbols = set([p.symbol for p in Position.objects.all()])
        strategy_symbols = set([s.symbol for s in StrategyResult.objects.all()])

        for symbol in position_symbols:
            if symbol in strategy_symbols:
                print 'using symbol: %s' % symbol
                self.position = Position.objects.filter(symbol=symbol).first()
                self.strategy_result = StrategyResult.objects.filter(symbol=symbol).first()
                break

    def test_blind_strategy_form_is_valid(self):
        """
        Test blind position form is valid
        """
        data = {
            'position': self.position.id,
            'strategy_result': self.strategy_result.id
        }
        print 'correct data',
        print data
        form = BlindPositionForm(data=data)
        self.assertTrue(form.is_valid())
        print 'blinding is success'

        # invalid
        data = {
            'position': 1,
            'strategy_result': 100
        }
        print 'invalid data',
        print data
        form = BlindPositionForm(data=data)
        self.assertFalse(form.is_valid())
        print 'invalid blinding...'

        # different symbol

        strategy_result = StrategyResult.objects.exclude(symbol='WFC').first()
        data = {
            'position': self.position.id,
            'strategy_result': strategy_result.id
        }
        print 'without correct symbol',
        print data
        form = BlindPositionForm()
        self.assertFalse(form.is_valid())
        print 'invalid blinding...'


class TestPositionReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.position = Position.objects.filter(symbol='WFC').last()
        self.date = self.position.stop

        #print self.position, self.date

    def test_view(self):
        """
        Test position report get correct values
        """
        response = self.client.get(
            reverse('admin:position_report', kwargs={'id': self.position.id, 'date': self.date})
        )

        keys = [
            'position', 'basic', 'stages', 'conditions', 'reports',
            'opinions', 'result', 'quant', 'historicals',
        ]

        for key in keys:
            pprint(response.context[key])


class TestDailyImport(TestUnitSetUp):
    def test_csv_option_import_view(self):
        """
        Test import thinkback csv option into db
        """
        date = '2015-10-12'

        print 'run daily import view...'
        self.client.get(reverse('admin:daily_import', kwargs={'date': date}))
