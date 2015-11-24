from statement.models import AccountTrade
from statement.position.stages.vertical.vertical import *
from statement.position.stages.tests import TestStage


class TestStageLongCallVertical(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('VERTICAL', 'LONG_CALL_VERTICAL')
        self.create_option_trade('VERTICAL', 'BUY', 1, 5.50, 2.15, contract='CALL', strike=105)
        self.create_option_trade('VERTICAL', 'SELL', -1, 3.35, 2.15, contract='CALL', strike=110)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageLongCallVertical(self.stock_trades)

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
        self.assertEqual(stage1.price, 105)
        self.assertEqual(stage1.lt_stage, 'MAX_LOSS')
        self.assertEqual(stage1.lt_amount, -215)
        self.assertEqual(stage1.e_stage, 'MAX_LOSS')
        self.assertEqual(stage1.e_amount, -215)
        self.assertEqual(stage1.gt_stage, 'LOSS')
        self.assertEqual(stage1.check_status(104), 'MAX_LOSS')
        self.assertEqual(stage1.check_status(105), 'MAX_LOSS')
        self.assertEqual(stage1.check_status(106), 'LOSS')

        stage2 = stages[1]
        self.assertEqual(float(stage2.price), 107.15)
        self.assertEqual(stage2.lt_stage, 'LOSS')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0)
        self.assertEqual(stage2.gt_stage, 'PROFIT')
        self.assertEqual(stage2.check_status(107.14), 'LOSS')
        self.assertEqual(stage2.check_status(107.15), 'EVEN')
        self.assertEqual(stage2.check_status(107.16), 'PROFIT')

        stage3 = stages[2]
        self.assertEqual(stage3.lt_stage, 'PROFIT')
        self.assertEqual(stage3.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage3.e_amount, 285)
        self.assertEqual(stage3.gt_stage, 'MAX_PROFIT')
        self.assertEqual(stage3.e_amount, 285)
        self.assertEqual(stage3.check_status(109), 'PROFIT')
        self.assertEqual(stage3.check_status(110), 'MAX_PROFIT')
        self.assertEqual(stage3.check_status(111), 'MAX_PROFIT')

        conditions = self.position.make_conditions()
        self.assertEqual(len(conditions), 5)
        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=104), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=105), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=106), 'LOSS')
        self.assertEqual(self.position.current_stage(price=107.14), 'LOSS')
        self.assertEqual(self.position.current_stage(price=107.15), 'EVEN')
        self.assertEqual(self.position.current_stage(price=107.16), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=109), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=110), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=111), 'MAX_PROFIT')


class TestStageShortCallVertical(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('VERTICAL', 'SHORT_CALL_VERTICAL')
        self.create_option_trade('VERTICAL', 'SELL', -1, 6.45, -2.65, contract='CALL', strike=115)
        self.create_option_trade('VERTICAL', 'BUY', 1, 3.80, -2.65, contract='CALL', strike=120)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageShortCallVertical(self.stock_trades)

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
        self.assertEqual(stage1.price, 115)
        self.assertEqual(stage1.lt_stage, 'MAX_PROFIT')
        self.assertEqual(stage1.lt_amount, 265)
        self.assertEqual(stage1.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage1.e_amount, 265)
        self.assertEqual(stage1.gt_stage, 'PROFIT')
        self.assertEqual(stage1.check_status(114), 'MAX_PROFIT')
        self.assertEqual(stage1.check_status(115), 'MAX_PROFIT')
        self.assertEqual(stage1.check_status(116), 'PROFIT')

        stage2 = stages[1]
        self.assertEqual(float(stage2.price), 117.35)
        self.assertEqual(stage2.lt_stage, 'PROFIT')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0)
        self.assertEqual(stage2.gt_stage, 'LOSS')
        self.assertEqual(stage2.check_status(117.34), 'PROFIT')
        self.assertEqual(stage2.check_status(117.35), 'EVEN')
        self.assertEqual(stage2.check_status(117.36), 'LOSS')

        stage3 = stages[2]
        self.assertEqual(float(stage3.price), 120)
        self.assertEqual(stage3.lt_stage, 'LOSS')
        self.assertEqual(stage3.e_stage, 'MAX_LOSS')
        self.assertEqual(stage3.e_amount, -235)
        self.assertEqual(stage3.gt_stage, 'MAX_LOSS')
        self.assertEqual(stage3.gt_amount, -235)
        self.assertEqual(stage3.check_status(119), 'LOSS')
        self.assertEqual(stage3.check_status(120), 'MAX_LOSS')
        self.assertEqual(stage3.check_status(121), 'MAX_LOSS')

        conditions = self.position.make_conditions()
        self.assertEqual(len(conditions), 5)
        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=114), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=115), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=116), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=117.34), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=117.35), 'EVEN')
        self.assertEqual(self.position.current_stage(price=117.36), 'LOSS')
        self.assertEqual(self.position.current_stage(price=119), 'LOSS')
        self.assertEqual(self.position.current_stage(price=120), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=121), 'MAX_LOSS')


class TestStageLongPutVertical(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('VERTICAL', 'LONG_PUT_VERTICAL')
        self.create_option_trade('VERTICAL', 'SELL', -1, 0.32, 1.02, contract='PUT', strike=72.50)
        self.create_option_trade('VERTICAL', 'BUY', 1, 1.34, 1.02, contract='PUT', strike=77.50)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageLongPutVertical(self.stock_trades)

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
        self.assertEqual(stage1.price, 72.5)
        self.assertEqual(stage1.lt_stage, 'MAX_PROFIT')
        self.assertEqual(stage1.lt_amount, 398)
        self.assertEqual(stage1.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage1.e_amount, 398)
        self.assertEqual(stage1.gt_stage, 'PROFIT')
        self.assertEqual(stage1.check_status(72.4), 'MAX_PROFIT')
        self.assertEqual(stage1.check_status(72.5), 'MAX_PROFIT')
        self.assertEqual(stage1.check_status(72.6), 'PROFIT')

        stage2 = stages[1]
        self.assertEqual(float(stage2.price), 76.48)
        self.assertEqual(stage2.lt_stage, 'PROFIT')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0)
        self.assertEqual(stage2.gt_stage, 'LOSS')
        self.assertEqual(stage2.check_status(76.47), 'PROFIT')
        self.assertEqual(stage2.check_status(76.48), 'EVEN')
        self.assertEqual(stage2.check_status(76.49), 'LOSS')

        stage3 = stages[2]
        self.assertEqual(float(stage3.price), 77.5)
        self.assertEqual(stage3.lt_stage, 'LOSS')
        self.assertEqual(stage3.e_stage, 'MAX_LOSS')
        self.assertEqual(stage3.e_amount, -102)
        self.assertEqual(stage3.gt_stage, 'MAX_LOSS')
        self.assertEqual(stage3.gt_amount, -102)
        self.assertEqual(stage3.check_status(77.4), 'LOSS')
        self.assertEqual(stage3.check_status(77.5), 'MAX_LOSS')
        self.assertEqual(stage3.check_status(77.6), 'MAX_LOSS')

        conditions = self.position.make_conditions()
        self.assertEqual(len(conditions), 5)
        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=72.4), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=72.5), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=72.6), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=76.47), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=76.48), 'EVEN')
        self.assertEqual(self.position.current_stage(price=76.49), 'LOSS')
        self.assertEqual(self.position.current_stage(price=77.4), 'LOSS')
        self.assertEqual(self.position.current_stage(price=77.5), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=77.6), 'MAX_LOSS')


class TestStageShortPutVertical(TestStage):
    def setUp(self):
        TestStage.setUp(self)

        self.create_position('VERTICAL', 'SHORT_PUT_VERTICAL')
        self.create_option_trade('VERTICAL', 'BUY', 1, 1.92, -2.84, contract='PUT', strike=200.00)
        self.create_option_trade('VERTICAL', 'SELL', -1, 4.76, -2.84, contract='PUT', strike=209.00)
        self.stock_trades = AccountTrade.objects.all()

        self.stage = StageShortPutVertical(self.stock_trades)

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
        self.assertEqual(stage1.price, 200)
        self.assertEqual(stage1.lt_stage, 'MAX_LOSS')
        self.assertEqual(stage1.lt_amount, -616)
        self.assertEqual(stage1.e_stage, 'MAX_LOSS')
        self.assertEqual(stage1.e_amount, -616)
        self.assertEqual(stage1.gt_stage, 'LOSS')
        self.assertEqual(stage1.check_status(199), 'MAX_LOSS')
        self.assertEqual(stage1.check_status(200), 'MAX_LOSS')
        self.assertEqual(stage1.check_status(201), 'LOSS')

        stage2 = stages[1]
        self.assertEqual(float(stage2.price), 206.16)
        self.assertEqual(stage2.lt_stage, 'LOSS')
        self.assertEqual(stage2.e_stage, 'EVEN')
        self.assertEqual(stage2.e_amount, 0)
        self.assertEqual(stage2.gt_stage, 'PROFIT')
        self.assertEqual(stage2.check_status(206.15), 'LOSS')
        self.assertEqual(stage2.check_status(206.16), 'EVEN')
        self.assertEqual(stage2.check_status(206.17), 'PROFIT')

        stage3 = stages[2]
        self.assertEqual(float(stage3.price), 209)
        self.assertEqual(stage3.lt_stage, 'PROFIT')
        self.assertEqual(stage3.e_stage, 'MAX_PROFIT')
        self.assertEqual(stage3.e_amount, 284)
        self.assertEqual(stage3.gt_stage, 'MAX_PROFIT')
        self.assertEqual(stage3.gt_amount, 284)
        self.assertEqual(stage3.check_status(208.9), 'PROFIT')
        self.assertEqual(stage3.check_status(209), 'MAX_PROFIT')
        self.assertEqual(stage3.check_status(209.1), 'MAX_PROFIT')

        conditions = self.position.make_conditions()
        self.assertEqual(len(conditions), 5)
        for condition in conditions:
            print condition

        # test current stage
        self.assertEqual(self.position.current_stage(price=199), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=200), 'MAX_LOSS')
        self.assertEqual(self.position.current_stage(price=201), 'LOSS')
        self.assertEqual(self.position.current_stage(price=206.15), 'LOSS')
        self.assertEqual(self.position.current_stage(price=206.16), 'EVEN')
        self.assertEqual(self.position.current_stage(price=206.17), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=208), 'PROFIT')
        self.assertEqual(self.position.current_stage(price=209), 'MAX_PROFIT')
        self.assertEqual(self.position.current_stage(price=210), 'MAX_PROFIT')