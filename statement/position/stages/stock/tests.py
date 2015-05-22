from statement.models import AccountTrade
from statement.position.stages.stock.stock import *
from statement.position.stages.tests import TestStage


class TestStageLongStock(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('STOCK', 'LONG_STOCK')
        self.create_stock_trade('BUY', 1, 20.17)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageLongStock(self.stock_trades)

    def test_create_stage(self):
        """
        Test create long stock stage
        """
        stage = self.stage.create()[0]

        print 'stage:', stage

        # add stages into position
        self.position.positionstage_set.add(stage)

        self.assertEqual(float(stage.price), 20.17)
        self.assertEqual(stage.check(20.16), 'LOSS')
        self.assertEqual(stage.check(20.17), 'EVEN')
        self.assertEqual(stage.check(20.18), 'PROFIT')

        conditions = self.position.make_conditions()

        for condition in conditions:
            print condition

        self.assertTrue(eval(conditions[0][1].format(x=20.16)))
        self.assertTrue(eval(conditions[1][1].format(x=20.17)))
        self.assertTrue(eval(conditions[2][1].format(x=20.18)))

        # test current stage
        self.assertEqual(self.position.current_stage(price=20.16), 'LOSS')
        self.assertEqual(self.position.current_stage(price=20.17), 'EVEN')
        self.assertEqual(self.position.current_stage(price=20.18), 'PROFIT')


class TestStageShortStock(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('STOCK', 'SHORT_STOCK')
        self.create_stock_trade('SELL', -1, 124.86)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageShortStock(self.stock_trades)

    def test_create_stage(self):
        """
        Test create short stock stage
        """
        stage = self.stage.create()[0]

        print 'stage:', stage

        # add stages into position
        self.position.positionstage_set.add(stage)

        self.assertEqual(float(stage.price), 124.86)
        self.assertEqual(stage.check(124.85), 'PROFIT')
        self.assertEqual(stage.check(124.86), 'EVEN')
        self.assertEqual(stage.check(124.87), 'LOSS')

        conditions = self.position.make_conditions()

        for condition in conditions:
            print condition

        self.assertTrue(eval(conditions[0][1].format(x=124.85)))
        self.assertTrue(eval(conditions[1][1].format(x=124.86)))
        self.assertTrue(eval(conditions[2][1].format(x=124.87)))

        # test current stage
        self.assertEqual(self.position.current_stage(price=124.85), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=124.86), 'EVEN')
        self.assertEqual(self.position.current_stage(price=124.87), 'LOSS')
