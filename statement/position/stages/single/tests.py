from statement.models import AccountTrade
from statement.position.stages.single.single import *
from statement.position.stages.tests import TestStage


class TestStageLongCall(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('SINGLE', 'LONG_CALL')
        self.create_option_trade('SINGLE', 'BUY', 1, 2.17, 2.17, contract='CALL', strike=204)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageLongCall(self.stock_trades)

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
        self.assertEqual(stage1.lt_amount, -217)
        self.assertEqual(stage1.e_stage, 'MAX_LOSS')
        self.assertEqual(stage1.e_amount, -217)
        self.assertEqual(stage1.gt_stage, 'LOSS')
        self.assertEqual(stage1.check_status(203.9), 'MAX_LOSS')
        self.assertEqual(stage1.check_status(204), 'MAX_LOSS')
        self.assertEqual(stage1.check_status(204.1), 'LOSS')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'LOSS')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0)
        self.assertEqual(stage2.gt_stage, 'PROFIT')
        self.assertEqual(stage2.check_status(206.16), 'LOSS')
        self.assertEqual(stage2.check_status(206.17), 'EVEN')
        self.assertEqual(stage2.check_status(206.18), 'PROFIT')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=203.9), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=204), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=204.1), 'LOSS')
        self.assertEqual(self.position.current_stage(price=206.16), 'LOSS')
        self.assertEqual(self.position.current_stage(price=206.17), 'EVEN')
        self.assertEqual(self.position.current_stage(price=206.18), 'PROFIT')


class TestStageNakedCall(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('SINGLE', 'NAKED_CALL')
        self.create_option_trade('SINGLE', 'SELL', -1, 0.74, 0.74, contract='CALL', strike=18.00)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageNakedCall(self.stock_trades)

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
        self.assertEqual(stage1.lt_amount, 74)
        self.assertEqual(stage1.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage1.e_amount, 74)
        self.assertEqual(stage1.gt_stage, 'PROFIT')
        self.assertEqual(stage1.check_status(17.9), 'MAX_PROFIT')
        self.assertEqual(stage1.check_status(18), 'MAX_PROFIT')
        self.assertEqual(stage1.check_status(18.1), 'PROFIT')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'PROFIT')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0)
        self.assertEqual(stage2.gt_stage, 'LOSS')
        self.assertEqual(stage2.check_status(18.73), 'PROFIT')
        self.assertEqual(stage2.check_status(18.74), 'EVEN')
        self.assertEqual(stage2.check_status(18.75), 'LOSS')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=17.9), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=18), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=18.1), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=18.73), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=18.74), 'EVEN')
        self.assertEqual(self.position.current_stage(price=18.75), 'LOSS')


class TestStageLongPut(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('SINGLE', 'LONG_PUT')
        self.create_option_trade('SINGLE', 'BUY', 1, 0.58, 0.58, contract='PUT', strike=335)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageLongPut(self.stock_trades)

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
        self.assertEqual(stage1.check_status(334.41), 'PROFIT')
        self.assertEqual(stage1.check_status(334.42), 'EVEN')
        self.assertEqual(stage1.check_status(334.43), 'LOSS')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'LOSS')
        self.assertEqual(stage2.e_stage, 'MAX_LOSS')
        self.assertEqual(stage2.e_amount, -58)
        self.assertEqual(stage2.gt_stage, 'MAX_LOSS')
        self.assertEqual(stage2.gt_amount, -58)
        self.assertEqual(stage2.check_status(334.99), 'LOSS')
        self.assertEqual(stage2.check_status(335), 'MAX_LOSS')
        self.assertEqual(stage2.check_status(335.1), 'MAX_LOSS')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=334.41), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=334.42), 'EVEN')
        self.assertEqual(self.position.current_stage(price=334.43), 'LOSS')
        self.assertEqual(self.position.current_stage(price=334.99), 'LOSS')
        self.assertEqual(self.position.current_stage(price=335), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=335.1), 'MAX_LOSS')


class TestStageNakedPut(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('SINGLE', 'NAKED_PUT')
        self.create_option_trade('SINGLE', 'SELL', -1, 0.25, 0.25, contract='PUT', strike=17.50)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageNakedPut(self.stock_trades)

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
        self.assertEqual(stage1.check_status(17.24), 'LOSS')
        self.assertEqual(stage1.check_status(17.25), 'EVEN')
        self.assertEqual(stage1.check_status(17.26), 'PROFIT')

        stage2 = stages[1]
        self.assertEqual(stage2.lt_stage, 'PROFIT')
        self.assertEqual(stage2.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage2.e_amount, 25)
        self.assertEqual(stage2.gt_stage, 'MAX_PROFIT')
        self.assertEqual(stage2.gt_amount, 25)
        self.assertEqual(stage2.check_status(17.49), 'PROFIT')
        self.assertEqual(stage2.check_status(17.5), 'MAX_PROFIT')
        self.assertEqual(stage2.check_status(17.51), 'MAX_PROFIT')

        conditions = self.position.make_conditions()

        self.assertEqual(len(conditions), 4)

        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=17.24), 'LOSS')
        self.assertEqual(self.position.current_stage(price=17.25), 'EVEN')
        self.assertEqual(self.position.current_stage(price=17.26), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=17.49), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=17.5), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=17.51), 'MAX_PROFIT')
