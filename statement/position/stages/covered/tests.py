from statement.models import AccountTrade
from statement.position.stages.covered.covered import *
from statement.position.stages.tests import TestStage


class TestStageCoveredCall(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('COVERED', 'COVERED_CALL')
        self.create_stock_trade('BUY', 100, 109.93, 109.57, 'COVERED')
        self.create_option_trade('COVERED', 'SELL', -1, 0.36, 109.57, contract='CALL', strike=115)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageCoveredCall(self.stock_trades)

    def test_create_stage(self):
        """
        Test create stage
        """
        stages = self.stage.create()

        # add stages into position
        for stage in stages:
            print stage
            self.position.positionstage_set.add(stage)
        print '\n' + '.' * 100 + '\n'

        stage1 = stages[0]
        self.assertEqual(stage1.lt_stage, 'LOSS')
        self.assertEqual(stage1.e_stage, 'EVEN')
        self.assertEqual(stage1.e_amount, 0.0)
        self.assertEqual(stage1.gt_stage, 'PROFIT')
        self.assertEqual(stage1.check(109.56), 'LOSS')
        self.assertEqual(stage1.check(109.57), 'EVEN')
        self.assertEqual(stage1.check(109.58), 'PROFIT')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'PROFIT')
        self.assertEqual(stage2.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage2.e_amount, 543)
        self.assertEqual(stage2.gt_stage, 'MAX_PROFIT')
        self.assertEqual(stage2.gt_amount, 543)
        self.assertEqual(stage2.check(114.9), 'PROFIT')
        self.assertEqual(stage2.check(115), 'MAX_PROFIT')
        self.assertEqual(stage2.check(115.1), 'MAX_PROFIT')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=109.56), 'LOSS')
        self.assertEqual(self.position.current_stage(price=109.57), 'EVEN')
        self.assertEqual(self.position.current_stage(price=109.58), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=114.9), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=115), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=115.1), 'MAX_PROFIT')


class TestStageProtectiveCall(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('COVERED', 'PROTECTIVE_CALL')
        self.create_stock_trade('SELL', -100, 113.68, -51.64, 'COVERED')
        self.create_option_trade('COVERED', 'BUY', 1, 1.19, -51.64, contract='CALL', strike=52.5)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageProtectiveCall(self.stock_trades)

    def test_create_stage(self):
        """
        Test create stage
        """
        stages = self.stage.create()

        # add stages into position
        for stage in stages:
            print stage
            self.position.positionstage_set.add(stage)
        print '\n' + '.' * 100 + '\n'

        stage1 = stages[0]
        self.assertEqual(stage1.lt_stage, 'PROFIT')
        self.assertEqual(stage1.e_stage, 'EVEN')
        self.assertEqual(stage1.e_amount, 0.0)
        self.assertEqual(stage1.gt_stage, 'LOSS')
        self.assertEqual(stage1.check(51.63), 'PROFIT')
        self.assertEqual(stage1.check(51.64), 'EVEN')
        self.assertEqual(stage1.check(51.65), 'LOSS')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'LOSS')
        self.assertEqual(stage2.e_stage, 'MAX_LOSS')
        self.assertEqual(stage2.e_amount, -86)
        self.assertEqual(stage2.gt_stage, 'MAX_LOSS')
        self.assertEqual(stage2.gt_amount, -86)
        self.assertEqual(stage2.check(52.4), 'LOSS')
        self.assertEqual(stage2.check(52.5), 'MAX_LOSS')
        self.assertEqual(stage2.check(52.6), 'MAX_LOSS')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=51.63), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=51.64), 'EVEN')
        self.assertEqual(self.position.current_stage(price=51.65), 'LOSS')
        self.assertEqual(self.position.current_stage(price=52.4), 'LOSS')
        self.assertEqual(self.position.current_stage(price=52.5), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=52.6), 'MAX_LOSS')


class TestStageCoveredPut(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('COVERED', 'COVERED_PUT')
        self.create_stock_trade('SELL', -100, 27.71, 27.86, 'COVERED')
        self.create_option_trade('COVERED', 'SELL', -1, 0.15, 27.86, contract='PUT', strike=26)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageCoveredPut(self.stock_trades)

    def test_create_stage(self):
        """
        Test create stage
        """
        stages = self.stage.create()

        # add stages into position
        for stage in stages:
            print stage
            self.position.positionstage_set.add(stage)
        print '\n' + '.' * 100 + '\n'

        stage1 = stages[0]
        self.assertEqual(stage1.lt_stage, 'MAX_PROFIT')
        self.assertEqual(stage1.e_amount, 186)
        self.assertEqual(stage1.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage1.e_amount, 186)
        self.assertEqual(stage1.gt_stage, 'PROFIT')
        self.assertEqual(stage1.check(25.9), 'MAX_PROFIT')
        self.assertEqual(stage1.check(26), 'MAX_PROFIT')
        self.assertEqual(stage1.check(26.1), 'PROFIT')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'PROFIT')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0.0)
        self.assertEqual(stage2.gt_stage, 'LOSS')
        self.assertEqual(stage2.check(27.85), 'PROFIT')
        self.assertEqual(stage2.check(27.86), 'EVEN')
        self.assertEqual(stage2.check(27.87), 'LOSS')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=25.9), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=26), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=26.1), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=27.85), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=27.86), 'EVEN')
        self.assertEqual(self.position.current_stage(price=27.87), 'LOSS')


class TestStageProtectivePut(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('COVERED', 'PROTECTIVE_PUT')
        self.create_stock_trade('BUY', 100, 113.68, 116.18, 'COVERED')
        self.create_option_trade('COVERED', 'BUY', 1, 2.50, 116.18, contract='PUT', strike=115)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageProtectivePut(self.stock_trades)

    def test_create_stage(self):
        """
        Test create stage
        """
        stages = self.stage.create()

        # add stages into position
        for stage in stages:
            print stage
            self.position.positionstage_set.add(stage)
        print '\n' + '.' * 100 + '\n'

        stage1 = stages[0]
        self.assertEqual(stage1.lt_stage, 'MAX_LOSS')
        self.assertEqual(stage1.e_amount, -118)
        self.assertEqual(stage1.e_stage, 'MAX_LOSS')
        self.assertEqual(stage1.e_amount, -118)
        self.assertEqual(stage1.gt_stage, 'LOSS')
        self.assertEqual(stage1.check(114.9), 'MAX_LOSS')
        self.assertEqual(stage1.check(115), 'MAX_LOSS')
        self.assertEqual(stage1.check(115.1), 'LOSS')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'LOSS')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0.0)
        self.assertEqual(stage2.gt_stage, 'PROFIT')
        self.assertEqual(stage2.check(116.17), 'LOSS')
        self.assertEqual(stage2.check(116.18), 'EVEN')
        self.assertEqual(stage2.check(116.19), 'PROFIT')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=114.9), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=115), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=115.1), 'LOSS')
        self.assertEqual(self.position.current_stage(price=116.17), 'LOSS')
        self.assertEqual(self.position.current_stage(price=116.18), 'EVEN')
        self.assertEqual(self.position.current_stage(price=116.19), 'PROFIT')
