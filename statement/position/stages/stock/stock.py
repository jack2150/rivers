from statement.models import PositionStage
from statement.position.stages.stage import Stage


class StageLongStock(Stage):
    def create(self):
        """
        Create long stock stage
        :return: list of PositionStage
        """
        stage = PositionStage()
        stage.price = self.buy_stocks[0].net_price
        stage.lt_stage = 'LOSS'
        stage.lt_amount = 0.0
        stage.e_stage = 'EVEN'
        stage.e_amount = 0.0
        stage.gt_stage = 'PROFIT'
        stage.gt_amount = 0.0

        return [stage]


class StageShortStock(Stage):
    def create(self):
        """
        Create short stock stage
        :return: list of PositionStage
        """
        stage = PositionStage()
        stage.price = self.sell_stocks[0].net_price
        stage.lt_stage = 'PROFIT'
        stage.lt_amount = 0.0
        stage.e_stage = 'EVEN'
        stage.e_amount = 0.0
        stage.gt_stage = 'LOSS'
        stage.gt_amount = 0.0

        return [stage]

