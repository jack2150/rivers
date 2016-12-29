import os
from django.core.urlresolvers import reverse
from base.utests import TestUnitSetUp
from data.models import Underlying
from rivers.settings import QUOTE_DIR
import pandas as pd

from subtool.ticker.minute1.si_stat import SimpleIndicatorStat
from subtool.ticker.minute1.views import get_minute1_data


class TestMinute1SiReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'

    def test_minute1_si_report_view(self):
        """
        Test import thinkback csv option into db
        """
        # self.skipTest('Only test when need!')
        self.client.get(reverse('admin:minute1_si_report', kwargs={
            'symbol': self.symbol, 'date': '2016-11-23'
        }))


class TestSimpleIndicatorStat(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'

        df_minute1, df_day = get_minute1_data(self.symbol, '2016-11-22')

        self.si_stat = SimpleIndicatorStat(df_minute1, df_day)

    def test_bull_bear_count(self):
        """

        :return:
        """
        self.si_stat.bull_bear_count()































