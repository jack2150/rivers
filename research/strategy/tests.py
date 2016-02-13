import os

import pandas as pd
from base.tests import TestSetUp
from research.algorithm.models import Formula
from research.strategy.backtest import TradeBacktest
from research.strategy.models import Trade
from rivers.settings import RESEARCH, CLEAN


class TestTrade(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.trade = Trade(
            name='Stock',
            instrument='Stock',
            category='Stock',
            description='Buy or sell stock',
            path='stock.normal',
            arguments="{'side': 'follow'}"
        )

        self.trade.save()

    def test_get_args(self):
        """
        Test get arguments from trade
        """
        args = self.trade.get_args()

        print args

    def test_create_trade(self):
        """

        :return:
        """


        pass


