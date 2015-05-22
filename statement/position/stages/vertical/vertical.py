from statement.models import PositionStage
from statement.position.stages.stage import Stage


class StageLongCallVertical(Stage):
    def create(self):
        """
        Create long call vertical stage, no mini option
        :return: list of PositionStage
        """
        s1 = PositionStage()
        s1.price = self.buy_calls[0].strike
        s1.lt_stage = 'MAX_LOSS'
        s1.lt_amount = self.buy_calls[0].net_price * self.buy_calls[0].qty * 100 * -1
        s1.e_stage = 'MAX_LOSS'
        s1.e_amount = self.buy_calls[0].net_price * self.buy_calls[0].qty * 100 * -1
        s1.gt_stage = 'LOSS'

        s2 = PositionStage()
        s2.price = self.buy_calls[0].strike + self.buy_calls[0].net_price
        s2.lt_stage = 'LOSS'
        s2.e_stage = 'EVEN'
        s2.e_amount = 0
        s2.gt_stage = 'PROFIT'

        s3 = PositionStage()
        s3.price = self.sell_calls[0].strike
        s3.lt_stage = 'PROFIT'
        s3.e_stage = 'MAX_PROFIT'
        s3.e_amount = ((self.sell_calls[0].strike - self.buy_calls[0].strike - self.buy_calls[0].net_price)
                       * self.buy_calls[0].qty * 100)
        s3.gt_stage = 'MAX_PROFIT'
        s3.gt_amount = ((self.sell_calls[0].strike - self.buy_calls[0].strike - self.buy_calls[0].net_price)
                        * self.buy_calls[0].qty * 100)

        return [s1, s2, s3]


class StageShortCallVertical(Stage):
    def create(self):
        """
        Create short call vertical stage, no mini option
        :return: list of PositionStage
        """
        s1 = PositionStage()
        s1.price = self.sell_calls[0].strike
        s1.lt_stage = 'MAX_PROFIT'
        s1.lt_amount = self.sell_calls[0].net_price * self.sell_calls[0].qty * 100
        s1.e_stage = 'MAX_PROFIT'
        s1.e_amount = self.sell_calls[0].net_price * self.sell_calls[0].qty * 100
        s1.gt_stage = 'PROFIT'

        s2 = PositionStage()
        s2.price = self.buy_calls[0].strike + self.sell_calls[0].net_price
        s2.lt_stage = 'PROFIT'
        s2.e_stage = 'EVEN'
        s2.e_amount = 0
        s2.gt_stage = 'LOSS'

        s3 = PositionStage()
        s3.price = self.buy_calls[0].strike
        s3.lt_stage = 'LOSS'
        s3.e_stage = 'MAX_LOSS'
        s3.e_amount = ((self.buy_calls[0].strike - self.sell_calls[0].strike
                        - abs(self.sell_calls[0].net_price)) * self.sell_calls[0].qty * 100)
        s3.gt_stage = 'MAX_LOSS'
        s3.gt_amount = ((self.buy_calls[0].strike - self.sell_calls[0].strike
                         - abs(self.sell_calls[0].net_price)) * self.sell_calls[0].qty * 100)

        return [s1, s2, s3]


class StageLongPutVertical(Stage):
    def create(self):
        """
        Create long put vertical stage, no mini option
        :return: list of PositionStage
        """
        s1 = PositionStage()
        s1.price = self.sell_puts[0].strike
        s1.lt_stage = 'MAX_PROFIT'
        s1.lt_amount = ((self.buy_puts[0].strike - self.sell_puts[0].strike
                         - self.sell_puts[0].net_price) * self.buy_puts[0].qty * 100)
        s1.e_stage = 'MAX_PROFIT'
        s1.e_amount = ((self.buy_puts[0].strike - self.sell_puts[0].strike
                        - self.sell_puts[0].net_price) * self.buy_puts[0].qty * 100)
        s1.gt_stage = 'PROFIT'

        s2 = PositionStage()
        s2.price = self.buy_puts[0].strike - self.sell_puts[0].net_price
        s2.lt_stage = 'PROFIT'
        s2.e_stage = 'EVEN'
        s2.e_amount = 0
        s2.gt_stage = 'LOSS'

        s3 = PositionStage()
        s3.price = self.buy_puts[0].strike
        s3.lt_stage = 'LOSS'
        s3.e_stage = 'MAX_LOSS'
        s3.e_amount = self.sell_puts[0].net_price * self.sell_puts[0].qty * 100
        s3.gt_stage = 'MAX_LOSS'
        s3.gt_amount = self.sell_puts[0].net_price * self.sell_puts[0].qty * 100

        return [s1, s2, s3]


class StageShortPutVertical(Stage):
    def create(self):
        """
        Create long put vertical stage, no mini option
        :return: list of PositionStage
        """
        s1 = PositionStage()
        s1.price = self.buy_puts[0].strike
        s1.lt_stage = 'MAX_LOSS'
        s1.lt_amount = ((self.sell_puts[0].strike - self.buy_puts[0].strike
                         + self.buy_puts[0].net_price) * self.sell_puts[0].qty * 100)
        s1.e_stage = 'MAX_LOSS'
        s1.e_amount = ((self.sell_puts[0].strike - self.buy_puts[0].strike
                        + self.buy_puts[0].net_price) * self.sell_puts[0].qty * 100)
        s1.gt_stage = 'LOSS'

        s2 = PositionStage()
        s2.price = self.sell_puts[0].strike + self.buy_puts[0].net_price
        s2.lt_stage = 'LOSS'
        s2.e_stage = 'EVEN'
        s2.e_amount = 0
        s2.gt_stage = 'PROFIT'

        s3 = PositionStage()
        s3.price = self.sell_puts[0].strike
        s3.lt_stage = 'PROFIT'
        s3.e_stage = 'MAX_PROFIT'
        s3.e_amount = self.sell_puts[0].net_price * self.sell_puts[0].qty * 100
        s3.gt_stage = 'MAX_PROFIT'
        s3.gt_amount = self.sell_puts[0].net_price * self.sell_puts[0].qty * 100

        return [s1, s2, s3]
