from statement.models import PositionStage
from statement.position.stages.stage import Stage


class StageCoveredCall(Stage):
    def create(self):
        """
        Create covered call stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = self.buy_stocks[0].net_price
        stage1.lt_stage = 'LOSS'
        stage1.e_stage = 'EVEN'
        stage1.e_amount = 0.0
        stage1.gt_stage = 'PROFIT'

        stage2 = PositionStage()
        stage2.price = self.sell_calls[0].strike
        stage2.lt_stage = 'PROFIT'
        stage2.e_stage = 'MAX_PROFIT'
        stage2.e_amount = ((self.sell_calls[0].strike - self.buy_stocks[0].net_price)
                           * self.buy_stocks[0].qty)
        stage2.gt_stage = 'MAX_PROFIT'
        stage2.gt_amount = ((self.sell_calls[0].strike - self.buy_stocks[0].net_price)
                            * self.buy_stocks[0].qty)

        return [stage1, stage2]


class StageProtectiveCall(Stage):
    def create(self):
        """
        Create protective call stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = abs(self.sell_stocks[0].net_price)
        stage1.lt_stage = 'PROFIT'
        stage1.e_stage = 'EVEN'
        stage1.e_amount = 0.0
        stage1.gt_stage = 'LOSS'

        stage2 = PositionStage()
        stage2.price = self.buy_calls[0].strike
        stage2.lt_stage = 'LOSS'
        stage2.e_stage = 'MAX_LOSS'
        stage2.e_amount = ((abs(self.sell_stocks[0].net_price) - self.buy_calls[0].strike)
                           * self.sell_stocks[0].qty * -1)
        stage2.gt_stage = 'MAX_LOSS'
        stage2.gt_amount = ((abs(self.sell_stocks[0].net_price) - self.buy_calls[0].strike)
                            * self.sell_stocks[0].qty * -1)

        print self.sell_stocks[0].net_price, self.buy_calls[0].strike

        return [stage1, stage2]


class StageCoveredPut(Stage):
    def create(self):
        """
        Create covered put stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = self.sell_puts[0].strike
        stage1.lt_stage = 'MAX_PROFIT'
        stage1.lt_amount = ((self.sell_puts[0].strike - self.sell_stocks[0].net_price)
                            * self.sell_stocks[0].qty)
        stage1.e_stage = 'MAX_PROFIT'
        stage1.e_amount = ((self.sell_puts[0].strike - self.sell_stocks[0].net_price)
                           * self.sell_stocks[0].qty)
        stage1.gt_stage = 'PROFIT'

        stage2 = PositionStage()
        stage2.price = self.sell_stocks[0].net_price
        stage2.lt_stage = 'PROFIT'
        stage2.e_stage = 'EVEN'
        stage2.e_amount = 0.0
        stage2.gt_stage = 'LOSS'

        return [stage1, stage2]


class StageProtectivePut(Stage):
    def create(self):
        """
        Create protective put stage, no mini option
        :return: list of PositionStage
        """
        stage1 = PositionStage()
        stage1.price = self.buy_puts[0].strike
        stage1.lt_stage = 'MAX_LOSS'
        stage1.lt_amount = ((self.buy_stocks[0].net_price - self.buy_puts[0].strike)
                            * self.buy_stocks[0].qty * -1)
        stage1.e_stage = 'MAX_LOSS'
        stage1.e_amount = ((self.buy_stocks[0].net_price - self.buy_puts[0].strike)
                           * self.buy_stocks[0].qty * -1)
        stage1.gt_stage = 'LOSS'

        stage2 = PositionStage()
        stage2.price = self.buy_stocks[0].net_price
        stage2.lt_stage = 'LOSS'
        stage2.e_stage = 'EVEN'
        stage2.e_amount = 0.0
        stage2.gt_stage = 'PROFIT'

        return [stage1, stage2]