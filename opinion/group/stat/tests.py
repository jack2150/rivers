import numpy as np
import pandas as pd
from django.core.urlresolvers import reverse
from base.ufunc import ts
from base.utests import TestUnitSetUp
from data.get_data import GetData
from opinion.group.stat.stats import ReportStatPrice

TEST_SYMBOL = 'LUV'
df_stock = GetData.get_stock_data(TEST_SYMBOL)


# noinspection PyAttributeOutsideInit
class TestStatPriceReport(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.report = ReportStatPrice(df_stock)

    def test_date_range(self):
        """
        Test main_stat calc
        """
        print 'before df_stock length: %d' % len(self.report.df_stock)
        report = ReportStatPrice(df_stock, date0='2010-01-01', date1='2016-12-31')
        print 'after df_stock length: %d' % len(report.df_stock)

    def test_main_stat(self):
        """
        Test main_stat calc
        """
        stat_data = self.report.main_stat()
        ts(pd.DataFrame(stat_data, index=[0]))

    def test_move_dist(self):
        """
        Test move distribution calc
        """
        df_group = self.report.move_dist()
        ts(df_group)

    def test_bday_dist(self):
        """
        Test hold bday calc
        """
        for days in (5, 20, 60):
            df_move = self.report.bday_dist(days)
            ts(df_move)

    def test_stem(self):
        """

        :return:
        """
        self.report.stem(1, 60)

    def test_report_view(self):
        """
        Test generate stock fundamental report
        """
        self.client.get(reverse('report_statprice', kwargs={
            'symbol': TEST_SYMBOL,
        }))
        """

        self.client.get(reverse('report_statstem', kwargs={
            'symbol': TEST_SYMBOL, 'percent': 1, 'bdays': 5,
        }))
        """


