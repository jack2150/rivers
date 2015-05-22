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
        stage.e_stage = 'EVEN'
        stage.gt_stage = 'PROFIT'

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
        stage.e_stage = 'EVEN'
        stage.gt_stage = 'LOSS'

        return [stage]

