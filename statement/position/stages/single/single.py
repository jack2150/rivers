from decimal import Decimal
from statement.models import PositionStage
from statement.position.stages.stage import Stage


class StageLongCall(Stage):
    def create(self):
        """
        Create long call stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = self.buy_calls[0].strike
        stage1.lt_stage = 'MAX_LOSS'
        stage1.lt_amount = self.buy_calls[0].net_price * self.buy_calls[0].qty * -100
        stage1.e_stage = 'MAX_LOSS'
        stage1.e_amount = stage1.lt_amount
        stage1.gt_stage = 'LOSS'
        stage1.gt_amount = stage1.lt_amount

        stage2 = PositionStage()
        stage2.price = self.buy_calls[0].strike + self.buy_calls[0].net_price
        stage2.lt_stage = 'LOSS'
        stage2.lt_amount = 0.0
        stage2.e_stage = 'EVEN'
        stage2.e_amount = 0.0
        stage2.gt_stage = 'PROFIT'
        stage2.gt_amount = 0.0

        return [stage1, stage2]


class StageNakedCall(Stage):
    def create(self):
        """
        Create naked call stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = self.sell_calls[0].strike
        stage1.lt_stage = 'MAX_PROFIT'
        stage1.lt_amount = self.sell_calls[0].net_price * self.sell_calls[0].qty * -100
        stage1.e_stage = 'MAX_PROFIT'
        stage1.e_amount = stage1.lt_amount
        stage1.gt_stage = 'PROFIT'
        stage1.gt_amount = stage1.lt_amount

        stage2 = PositionStage()
        stage2.price = self.sell_calls[0].strike + self.sell_calls[0].net_price
        stage2.lt_stage = 'PROFIT'
        stage2.lt_amount = 0.0
        stage2.e_stage = 'EVEN'
        stage2.e_amount = 0.0
        stage2.gt_stage = 'LOSS'
        stage2.gt_amount = 0.0

        return [stage1, stage2]


class StageLongPut(Stage):
    def create(self):
        """
        Create long put stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = self.buy_puts[0].strike - self.buy_puts[0].net_price
        stage1.lt_stage = 'PROFIT'
        stage1.lt_amount = 0.0
        stage1.e_stage = 'EVEN'
        stage1.e_amount = 0.0
        stage1.gt_stage = 'LOSS'
        stage1.gt_amount = 0.0

        stage2 = PositionStage()
        stage2.price = self.buy_puts[0].strike
        stage2.lt_stage = 'LOSS'
        stage2.lt_amount = self.buy_puts[0].net_price * self.buy_puts[0].qty * -100
        stage2.e_stage = 'MAX_LOSS'
        stage2.e_amount = stage2.lt_amount
        stage2.gt_stage = 'MAX_LOSS'
        stage2.gt_amount = stage2.lt_amount

        return [stage1, stage2]


class StageNakedPut(Stage):
    def create(self):
        """
        Create naked put stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = self.sell_puts[0].strike - self.sell_puts[0].net_price
        stage1.lt_stage = 'LOSS'
        stage1.lt_amount = 0.0
        stage1.e_stage = 'EVEN'
        stage1.e_amount = 0.0
        stage1.gt_stage = 'PROFIT'
        stage1.gt_amount = 0.0

        stage2 = PositionStage()
        stage2.price = self.sell_puts[0].strike
        stage2.lt_stage = 'PROFIT'
        stage2.lt_amount = self.sell_puts[0].net_price * self.sell_puts[0].qty * -100
        stage2.e_stage = 'MAX_PROFIT'
        stage2.e_amount = stage2.lt_amount
        stage2.gt_stage = 'MAX_PROFIT'
        stage2.gt_amount = stage2.lt_amount


        return [stage1, stage2]